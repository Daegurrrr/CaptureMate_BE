# ai/classifier_model_v2.py

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "hur03/capturemate-category-classifier"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()

ID2LABEL = model.config.id2label

# 영어 → 한국어 카테고리 매핑
LABEL_MAP = {
    "shopping": "쇼핑",
    "place": "장소",
    "schedule": "일정",
    "memo": "메모",
    "etc": "기타"
}

def predict_category(ocr_text: str) -> dict:
    if not ocr_text or not ocr_text.strip():
        return {"category": "기타", "confidence": 0.0}

    inputs = tokenizer(
        ocr_text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256,
    )

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0]

    pred_id = int(torch.argmax(probs).item())
    confidence = float(probs[pred_id].item())

    return {
        "category": LABEL_MAP.get(ID2LABEL[pred_id], "기타"),  # 한국어로 변환
        "confidence": round(confidence, 4),
    }