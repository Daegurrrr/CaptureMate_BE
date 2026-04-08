import boto3
from dotenv import load_dotenv
import os

load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

try:
    response = s3.list_buckets()
    print("✅ S3 연결 성공!")
    for bucket in response['Buckets']:
        print(f"  버킷: {bucket['Name']}")
except Exception as e:
    print(f"❌ 연결 실패: {e}")