import boto3 
from config import S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME
from botocore.exceptions import ClientError

s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,  # R2 requires HTTPS
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name="auto"  # required for R2
)

def bucket_exists() -> bool:
    try:
        # R2-compatible: try listing objects
        s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, MaxKeys=1)
        return True
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in ("NoSuchBucket", "404"):
            print(f"Bucket '{S3_BUCKET_NAME}' not found.")
            return False
        else:
            print("Unexpected error:", e)
            raise
