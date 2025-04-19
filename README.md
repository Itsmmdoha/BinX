# Binx API

Binx is an API designed to provide a simple and secure file storage system. The front end is under development, and this project currently focuses on the backend API, which allows users to create vaults, upload and download files, and manage their storage. Binx focuses on simplicity. The user just provides  a `vult name` and a `password` for the vault that's it, not emails no data, no strings attached.

**Note**: The API is under constant development, and while it's not fully ready, it's almost there. The frontend will be coming soon!

## Features
- Create a vault by providing a name and password.
- Log in to an existing vault.
- Upload files to your vault with automatic storage size management.
- Download files from your vault using a presigned URL.
- Delete files from your vault.

## Tech Stack
- **FastAPI**: For building the API.
- **PostgreSQL**: For storing vault and file metadata.
- **MinIO**: For object storage, acting as an S3-compatible service.
- **Boto3**: AWS SDK for interacting with MinIO.
- **Pydantic**: For data validation and serialization.
- **SQLAlchemy**: For interacting with the database.

## Endpoints

### Vault Operations

#### `GET /`
- **Description**: Lists all vaults in the database.
- **Response**: A list of vaults with metadata.

#### `POST /vault/create`
- **Description**: Create a new vault by providing a name and password.
- **Request Body**:
  ```json
  {
    "vault": "vault_name",
    "password": "your_password"
  }
  ```
- **Response**:
  - Success: `{"message": "vault created successfully"}`
  - Conflict: `{"detail": "Already exists"}`

#### `POST /vault/login`
- **Description**: Log in to a vault using the vault name and password. This will return an access token.
- **Request Body**:
  ```json
  {
    "vault": "vault_name",
    "password": "your_password"
  }
  ```
- **Response**:
  ```json
  {
    "message": "login successful",
    "access_token": "your_token",
    "token_type": "bearer"
  }
  ```
  - Unauthorized: `{"detail": "Invalid Credentials"}`

#### `GET /vault/fetch`
- **Description**: Fetch the list of files in a vault. Requires a valid JWT token.
- **Response**:
  ```json
  {
    "vault": {
      "vault": "vault_name",
      "date_created": "timestamp",
      "size": 1000,
      "used_storage": 500
    },
    "files": [
      {
        "file": "file1.txt",
        "size": 100,
        "date_created": "timestamp"
      }
    ]
  }
  ```
  - Unauthorized: `{"detail": "Invalid or Expired Token"}`
  - Forbidden: `{"detail": "Forbidden"}`

### File Operations

#### `POST /file/upload`
- **Description**: Upload a file to the vault. Requires a valid JWT token.
- **Request Body**: Multipart file upload.
- **Response**:
  ```json
  {
    "message": "File uploaded successfully"
  }
  ```
  - Unauthorized: `{"detail": "Invalid or Expired Token"}`
  - Forbidden: `{"detail": "Forbidden"}`
  - Server Error: `{"detail": "File Upload Failed"}`

#### `GET /file/download/{file_name}`
- **Description**: Download a file from the vault using a presigned URL. Requires a valid JWT token.
- **Response**:
  ```json
  {
    "download_url": "presigned_url",
    "valid_for_seconds": 600
  }
  ```
  - Unauthorized: `{"detail": "Invalid or Expired Token"}`
  - Forbidden: `{"detail": "Forbidden"}`
  - Not Found: `{"detail": "File not found"}`
  - Server Error: `{"detail": "Error Generating Download Link"}`

#### `GET /file/delete/{file_name}`
- **Description**: Delete a file from the vault. Requires a valid JWT token.
- **Response**:
  ```json
  {
    "message": "file deleted successfully"
  }
  ```
  - Unauthorized: `{"detail": "Invalid or Expired Token"}`
  - Forbidden: `{"detail": "Forbidden"}`
  - Not Found: `{"detail": "File not found"}`

## How to Run the Development Server

### Prerequisites
- Python 3.8 or higher
- Docker for MinIO and PostgreSQL

### Step 1: Set up the environment
Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### Step 2: Install dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### Step 3: Run Docker Compose
Before running the FastAPI server, you need to set up the required services (MinIO and PostgreSQL) using Docker Compose:
```bash
docker-compose up
```
This will start MinIO on `localhost:9000` and PostgreSQL on `localhost:5432`.

### Step 4: Run the FastAPI Server
After the Docker services are running, start the FastAPI development server:
```bash
uvicorn main:app --reload
```

### Step 5: Access the API
The FastAPI server will be running on `http://localhost:8000`. You can access the documentation at:
```
http://localhost:8000/docs
```

## Future Plans
- Frontend development will be coming soon.
- More advanced features such as role-based access control and detailed logging.

## License
This project is open-source and available under the MIT License. See the LICENSE file for more details.
