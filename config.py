import os

# Frontend configuration
# Environment variable: FRONTEND_HOST
FRONTEND_HOST = os.environ.get("FRONTEND_HOST", "http://localhost:3000")

# PostgreSQL database configuration
# Environment variable: DATABASE_URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://user:password@localhost:5432/binx"
)

# S3/MinIO (development) configuration
# Environment variable: S3_ENDPOINT
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT", "http://localhost:9000")

# Environment variable: S3_ACCESS_KEY
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "minioadmin")

# Environment variable: S3_SECRET_KEY
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "minioadmin")

# Environment variable: S3_BUCKET_NAME
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "binx")

# JWT Secret Key configuration
# Environment variable: JWT_SECRET_KEY
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key")
