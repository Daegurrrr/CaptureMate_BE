# ai/classifier_model.py

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "hur03/capturemate-category-classifier"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()

ID2LABEL = model.config.id2label


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
        "category": ID2LABEL[pred_id],
        "confidence": round(confidence, 4),
    }