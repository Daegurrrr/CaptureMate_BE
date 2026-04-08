# AWS S3 이미지 업로드/삭제 로직
import boto3
from app.core.config import settings

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

def upload_image(file, filename: str) -> str:
    s3_client.upload_fileobj(file, settings.S3_BUCKET_NAME, filename)
    url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
    return url