import boto3 
from config import MINIO_ENDPOINT, ACCESS_KEY, SECRET_KEY, BUCKET_NAME

s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)

def create_bucket_if_not_exists() -> None:
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
    except:
        s3_client.create_bucket(Bucket=BUCKET_NAME)
