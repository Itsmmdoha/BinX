# Binx API

**Binx** is a lightweight, secure backend API designed for file storage. The API allows users to create personalized “vaults” with a name and password, then store, retrieve, and manage their files with simplicity and security. The frontend is under development, making the API central to file operations while ensuring minimal onboarding friction—no emails or extraneous data required.

> **Note:** The API is under active development. While core features are operational, the frontend is coming soon along with advanced functionalities such as role-based access control and detailed logging.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [API Endpoints](#api-endpoints)
  - [Vault Operations](#vault-operations)
  - [File Operations](#file-operations)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running with Docker Compose](#running-with-docker-compose)
  - [Starting the Server](#starting-the-server)
- [Future Plans](#future-plans)
- [License](#license)

---

## Features

- **Vault Creation:** Create a vault using just a name and a password.
- **Authentication:** Securely log in to an existing vault to obtain an access token.
- **File Management:** Upload, fetch, download (via presigned URL), rename, and delete files.
- **Storage Management:** Automatic handling of storage limits when uploading files.

---

## Tech Stack

- **FastAPI:** The framework used to build the backend API.
- **PostgreSQL:** Stores vault and file metadata.
- **MinIO:** Provides S3-compatible object storage.
- **Boto3:** AWS SDK used for interacting with MinIO.
- **Pydantic:** Ensures robust data validation and serialization.
- **SQLAlchemy:** Handles database operations with PostgreSQL.

---

## API Endpoints

The API is documented via a Redoc interface, with endpoints defined per the OpenAPI 3.1.0 specification. Below is a summary of the key endpoints, grouped by operation type.

### Vault Operations

- **List Vaults**  
  **Endpoint:** `GET /`  
  **Description:** Retrieves a list of all vaults along with their metadata.

- **Create Vault**  
  **Endpoint:** `POST /vault/create`  
  **Request Body:**  
  ```json
  {
    "vault": "vault_name",
    "password": "your_password"
  }
  ```  
  **Responses:**  
  - **200:** Vault created successfully.  
    ```json
    {"message": "vault created successfully"}
    ```  
  - **409:** Vault already exists.  
    ```json
    {"detail": "Already exists"}
    ```  

- **Login to Vault**  
  **Endpoint:** `POST /vault/login`  
  **Request Body:**  
  ```json
  {
    "vault": "vault_name",
    "password": "your_password"
  }
  ```  
  **Responses:**  
  - **200:** Login successful with an access token returned.  
    ```json
    {
      "message": "login successful",
      "access_token": "your_token",
      "token_type": "bearer"
    }
    ```  
  - **401:** Invalid credentials.  
    ```json
    {"detail": "Invalid Credentials"}
    ```

- **Fetch File List from Vault**  
  **Endpoint:** `GET /vault/fetch`  
  **Requirements:** Valid JWT token via HTTP Bearer authorization.  
  **Response:** Returns vault metadata and a list of files with their details.  
  - **200:**  
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
          "file_id": "uuid",
          "size": 100,
          "date_created": "timestamp"
        }
      ]
    }
    ```  
  - **401/403:** Returns error details for invalid or expired tokens or insufficient permissions.

### File Operations

- **Upload File**  
  **Endpoint:** `POST /file/upload`  
  **Request Body:** Multipart form-data containing the file.  
  **Requirements:** Valid JWT token via HTTP Bearer authorization.  
  **Responses:**  
  - **200:**  
    ```json
    {"message": "File uploaded successfully"}
    ```  
  - **401/403/500:** Returns error details for authentication issues, forbidden access, or server errors.

- **Download File**  
  **Endpoint:** `GET /file/{file_id}`  
  **Path Parameter:**  
  - `file_id` (UUID format)  
  **Requirements:** Valid JWT token via HTTP Bearer authorization.  
  **Response:**  
  - **200:** Provides a presigned download URL and the validity duration (in seconds).  
    ```json
    {
      "download_url": "presigned_url",
      "valid_for_seconds": 600
    }
    ```  
  - **401/403/404/500:** Returns error details as appropriate.

- **Rename File**  
  **Endpoint:** `PUT /file/{file_id}`  
  **Path Parameter:**  
  - `file_id` (UUID format)  
  **Request Body:**  
  ```json
  {
    "new_name": "desired_new_filename.ext"
  }
  ```  
  **Requirements:** Valid JWT token via HTTP Bearer authorization.  
  **Response:**  
  - **200:**  
    ```json
    {"message": "file renamed successfully"}
    ```  
  - **401/403/404:** Returns error details if the operation fails.

- **Delete File**  
  **Endpoint:** `DELETE /file/{file_id}`  
  **Path Parameter:**  
  - `file_id` (UUID format)  
  **Requirements:** Valid JWT token via HTTP Bearer authorization.  
  **Response:**  
  - **200:**  
    ```json
    {"message": "file deleted successfully"}
    ```  
  - **401/403/404:** Returns error details if authentication fails or file is not found.

---

## Getting Started

### Prerequisites

- **Python 3.8 or higher**
- **Docker** (for running MinIO and PostgreSQL)

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://your-repo-url.git
   cd binx-api
   ```

2. **Create a Virtual Environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

### Running with Docker Compose

Before running the FastAPI server, you need to start MinIO and PostgreSQL with Docker Compose:

```bash
docker-compose up
```

This will launch:
- **MinIO:** Accessible on [http://localhost:9000](http://localhost:9000)
- **PostgreSQL:** Accessible on [http://localhost:5432](http://localhost:5432)

### Starting the Server

Once the dependencies and services are set up, start the FastAPI development server:

```bash
uvicorn app:app --reload
```

Access the API documentation via:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Redoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Future Plans

- **Frontend Integration:** A user-friendly interface will be released soon.
- **Enhanced Security Features:** Role-based access control (RBAC) and better logging will be integrated.
- **Additional Endpoints & Metrics:** Extended API operations to include more detailed file and vault management features.

---

## License

This project is open-source and available under the [MIT License](./LICENSE).

