# Binx API

**Binx** is a fast, secure, and minimal backend API for file vault management. Users create vaults (with optional guest access), store files in an S3‑compatible bucket, and manage file metadata—no emails, no fuss.

> **Status:** Active development
>
> * Core features: Vault creation, dual-mode login (guest/owner), file CRUD, visibility controls, storage quotas.
> * Upcoming: Frontend UI, granular RBAC, audit logging, shareable links.

---

## 🚀 Features

* **Vaults**: Create named vaults protected by passwords.
* **Dual-Mode Login**: Same endpoint returns a JWT as *guest* (read-only public files) or *owner* (full access).
* **File Operations**:

  * Upload (thread‑pooled S3 client)
  * Download via presigned URLs (10‑minute expiry)
  * Rename and update visibility (`public`/`private`)
  * Delete with automatic storage reclamation
* **Storage Quota**: Prevent uploads when exceeding per‑vault limits.
* **Visibility Control**: Owners flag files as `public` or `private` via an Enum.

---

## 🛠️ Tech Stack

| Component       | Technology      |
| --------------- | --------------- |
| Framework       | FastAPI         |
| Validation      | Pydantic        |
| Database        | PostgreSQL      |
| ORM             | SQLAlchemy      |
| Object Storage  | MinIO (S3 API)  |
| Storage SDK     | Boto3           |
| Auth & Security | JWT, HTTPBearer |

---

## 🔗 API Endpoints

### Auth & Vault

| Method | Path            | Access     | Description                                      |
| ------ | --------------- | ---------- | ------------------------------------------------ |
| GET    | `/`             | Public     | List all vaults                                  |
| POST   | `/vault/create` | Public     | Create vault                                     |
| POST   | `/vault/login`  | Public     | Login as guest/owner ⇒ returns JWT token         |
| GET    | `/vault/fetch`  | Bearer JWT | Get vault info + file list (public vs all files) |

#### Create Vault

* **Request Body**:

  ```json
  { "vault": "myvault", "password": "secret" }
  ```
* **Responses**:

  * `200 OK`: `{ "message": "vault created successfully" }`
  * `409 Conflict`: `{ "detail": "Already exists" }`

#### Login to Vault

* **Request Body** (guest):

  ```json
  { "vault": "myvault" }
  ```

* **Request Body** (owner):

  ```json
  { "vault": "myvault", "password": "secret" }
  ```

* **Successful Response** (`200 OK`):

  ```json
  {
    "message": "Login as guest successful" | "Login successful",
    "access_token": "<token>",
    "token_type": "bearer"
  }
  ```

* `401 Unauthorized` (bad password)

* `404 Not Found` (vault missing)

#### Fetch Vault Data

* **Auth**: `Authorization: Bearer <token>`
* **Response Model**: `vaultModel`

  ```json
  {
    "vault": { "vault": "myvault", "date_created": "...", "size": 1000, "used_storage": 200 },
    "files": [
      {
        "file": "report.pdf",
        "visibility": "public",
        "file_id": "...",
        "size": 500,
        "date_created": "..."
      }
    ]
  }
  ```

---

### File Operations

| Method | Path              | Access     | Description                   |
| ------ | ----------------- | ---------- | ----------------------------- |
| POST   | `/file/upload`    | Owner JWT  | Upload file (enforced quota)  |
| GET    | `/file/{file_id}` | Bearer JWT | Download file (presigned URL) |
| PUT    | `/file/{file_id}` | Owner JWT  | Rename or change visibility   |
| DELETE | `/file/{file_id}` | Owner JWT  | Delete file & free storage    |

#### Upload File

* **Form Data**: field `file`: file to upload
* **Permissions**: owner only
* **Storage Check**: returns  message on quota exceed
* **Success**: `200 OK` `{ "message": "File uploaded successfully" }`
* **Errors**: `403 Forbidden`, `500 Internal Server Error`

#### Download File

* **URL**: `/file/{file_id}`
* **Response**: `{ "download_url": "...", "valid_for_seconds": 600 }`
* **Errors**: `404 Not Found`, `500 Internal Server Error`

#### Rename / Update Visibility

* **Request Body**:

  ```json
  { "new_name": "new.pdf", "visibility": "private" }
  ```
* **Success**: `200 OK` `{ "message": "File updated successfully" }`
* **Errors**: `403 Forbidden`, `404 Not Found`

#### Delete File

* **URL**: `/file/{file_id}`
* **Success**: `200 OK` `{ "message": "file deleted successfully" }`
* **Errors**: `403 Forbidden`, `404 Not Found`

---

## ⚙️ Setup & Development

### Prerequisites

* **Python** ≥ 3.8
* **Docker & Docker Compose**



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

## 🌟 Future Plans

* **Frontend**: Web UI for vault & file management.
* **Granular RBAC**: Roles beyond owner/guest (e.g., admin).
* **Audit Logging**: Track actions and access patterns.
* **Shareable Links**: Secure public file links with tokens.

---

## 📄 License

Released under the MIT License. See [LICENSE](./LICENSE).
