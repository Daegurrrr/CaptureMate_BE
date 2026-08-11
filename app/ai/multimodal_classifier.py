# app/ai/multimodal_classifier.py

from io import BytesIO

import torch
import torch.nn as nn
import torch.nn.functional as F

from PIL import Image
from huggingface_hub import hf_hub_download
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    CLIPImageProcessor,
    CLIPVisionModelWithProjection,
)


# ==========================================
# 설정
# ==========================================

TEXT_MODEL_NAME = "hur03/capturemate-category-classifier-v1-5class"
IMAGE_MODEL_NAME = "hur03/capturemate-image-classifier-v1-5class"

TEXT_WEIGHT = 0.75
IMAGE_WEIGHT = 0.25

MAX_LENGTH = 256
NUM_LABELS = 5

LABEL2ID = {
    "schedule": 0,
    "shopping": 1,
    "place": 2,
    "memo": 3,
    "unknown": 4,
}

ID2LABEL = {
    value: key
    for key, value in LABEL2ID.items()
}

LABEL_MAP = {
    "schedule": "일정",
    "shopping": "쇼핑",
    "place": "장소",
    "memo": "메모",
    "unknown": "기타",
}

DEVICE = (
    "mps"
    if torch.backends.mps.is_available()
    else "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ==========================================
# CLIP 이미지 분류 모델
# 학습 코드와 동일한 구조
# ==========================================

class CLIPUIClassifier(nn.Module):

    def __init__(
        self,
        image_model_name: str,
        num_labels: int,
    ):
        super().__init__()

        self.image_model = (
            CLIPVisionModelWithProjection.from_pretrained(
                image_model_name
            )
        )

        image_feature_size = (
            self.image_model.config.projection_dim
        )

        self.classifier = nn.Sequential(
            nn.Linear(
                image_feature_size,
                256,
            ),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(
                256,
                128,
            ),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(
                128,
                num_labels,
            ),
        )

    def forward(self, pixel_values):
        image_output = self.image_model(
            pixel_values=pixel_values
        )

        image_feature = F.normalize(
            image_output.image_embeds,
            dim=1,
        )

        return self.classifier(image_feature)


# ==========================================
# 텍스트 모델 로드
# ==========================================

tokenizer = AutoTokenizer.from_pretrained(
    TEXT_MODEL_NAME
)

text_model = (
    AutoModelForSequenceClassification
    .from_pretrained(TEXT_MODEL_NAME)
    .to(DEVICE)
)

text_model.eval()


# ==========================================
# 이미지 모델 로드
# ==========================================

# Hugging Face에서 image_classifier.pt 다운로드
IMAGE_CHECKPOINT_PATH = hf_hub_download(
    repo_id=IMAGE_MODEL_NAME,
    filename="image_classifier.pt",
)

checkpoint = torch.load(
    IMAGE_CHECKPOINT_PATH,
    map_location=DEVICE,
)

image_base_model_name = checkpoint.get(
    "image_model_name",
    "openai/clip-vit-base-patch32",
)

image_processor = CLIPImageProcessor.from_pretrained(
    IMAGE_MODEL_NAME
)

image_model = CLIPUIClassifier(
    image_model_name=image_base_model_name,
    num_labels=checkpoint.get(
        "num_labels",
        NUM_LABELS,
    ),
)

image_model.load_state_dict(
    checkpoint["model_state_dict"]
)

image_model = image_model.to(DEVICE)
image_model.eval()


# ==========================================
# 텍스트 예측
# ==========================================

@torch.inference_mode()
def predict_text(ocr_text: str) -> dict:
    text = str(ocr_text).strip()

    if not text:
        text = "[EMPTY]"

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_LENGTH,
    )

    inputs = {
        key: value.to(DEVICE)
        for key, value in inputs.items()
    }

    logits = text_model(**inputs).logits

    probabilities = torch.softmax(
        logits,
        dim=-1,
    )[0]

    return {
        ID2LABEL[index]: probability.item()
        for index, probability in enumerate(probabilities)
    }


# ==========================================
# 이미지 예측
# ==========================================

@torch.inference_mode()
def predict_image(image_bytes: bytes) -> dict:
    image = Image.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    inputs = image_processor(
        images=image,
        return_tensors="pt",
    )

    pixel_values = inputs[
        "pixel_values"
    ].to(DEVICE)

    logits = image_model(
        pixel_values=pixel_values
    )

    probabilities = torch.softmax(
        logits,
        dim=-1,
    )[0]

    return {
        ID2LABEL[index]: probability.item()
        for index, probability in enumerate(probabilities)
    }


# ==========================================
# 최종 멀티모달 분류
# ==========================================

def predict_category(
    ocr_text: str,
    image_bytes: bytes,
) -> dict:

    text_scores = predict_text(
        ocr_text
    )

    image_scores = predict_image(
        image_bytes
    )

    final_scores = {}

    for label in LABEL2ID:
        final_scores[label] = (
            text_scores[label] * TEXT_WEIGHT
            + image_scores[label] * IMAGE_WEIGHT
        )

    predicted_label = max(
        final_scores,
        key=final_scores.get,
    )

    confidence = final_scores[
        predicted_label
    ]

    return {
        "category": LABEL_MAP[predicted_label],
        "confidence": round(
            float(confidence),
            4,
        ),
    }