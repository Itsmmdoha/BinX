# BinX API

[![GitHub Repo](https://github.com/Itsmmdoha/BinX)](https://github.com/Itsmmdoha/BinX)

BinX is a secure convenience focused file storage service designed for simplicity and speed. Create password-protected vaults to organize and safeguard your files. Access your vaults in two modes:

* **Owner**: Authenticate with both vault name and password to view, upload, delete, rename, and change visibility of all files (both `private` & `public`).
* **Guest**: Authenticate with vault name only to browse and download `public` files in read-only mode.

With BinX, you can **create vaults**, **log in (as guest or owner)**, **upload files**, **download**, **delete**, **rename**, and **change file visibility**.

> Status: Active Development

## 🛠️ Tech Stack

1. FastAPI (API)
2. Pydantic (Data Validation and Serializetion)
3. PostgreSQL (Database)
4. SQLAlchemy (ORM)
5. S3-compatible storage (MinIO)



## 📥 Getting Started

The BinX API depends on MinIO (for S3-compatible storage) and PostgreSQL. A `docker-compose.yml` is provided to spin up these services:

```yaml
services:
  minio:
    image: minio/minio:latest
    container_name: minio
    ports:
      - "9000:9000"  # S3 API endpoint
      - "9001:9001"  # Web UI
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    command: server --console-address ":9001" /data

  db:
    image: postgres:15
    container_name: postgres-db
    restart: always
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: binx
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  minio_data:
  postgres_data:
```

This compose file will:

* Launch **MinIO** on ports 9000 (S3 API) and 9001 (web console), using `minioadmin` credentials.
* Launch **PostgreSQL** 15 on port 5432 with a `binx` database.

1. **Clone the repository**

   ```bash
   git clone https://github.com/Itsmmdoha/BinX.git
   cd BinX
   ```
2. **Set up the environment**

   ```bash
   python -m venv venv
   source venv/bin/activate    # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Start required services**

   Make sure you have docker and docker-compose installed and run the following command
    ```bash
   docker-compose up -d
   ```

   * MinIO available at [http://localhost:9000](http://localhost:9000)
   * PostgreSQL at `localhost:5432`
5. **Launch the API server**

   ```bash
   uvicorn app:app --reload
   ```
6. **Access API docs**

   * Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Documentation

Here's the [API Documentation](./API_Docs.md)

## ⚙️ Future Plans

* **Frontend**: Web UI for vault & file management.
* **Granular RBAC**: Roles beyond owner/guest (e.g., admin).
* **Audit Logging**: Track actions and access patterns.
* **Shareable Links**: Secure public file links with tokens.


## 📄 License

Released under the MIT License. See [LICENSE](./LICENSE) for details.
