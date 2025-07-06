<div align="center">
  <a href="https://github.com/Itsmmdoha/BinX">
    <img src="https://binx.houndsec.net/logo.svg" alt="BinX Logo" width="150" height="150">
  </a>

  # _Store it_, with [BinX](https://binx.houndsec.net)

  <p>
    Secure, password‑protected vaults <a href="https://binx.houndsec.net"><strong>in your web browser</strong></a>.  
    <br>
    FastAPI + PostgreSQL + S3  
    <br><br>
    <a href="https://github.com/Itsmmdoha/BinX/issues">Report a bug</a>
    &nbsp;|&nbsp;
    <a href="https://github.com/Itsmmdoha/BinX/issues">Request feature</a>
  </p>
</div>
<br>


# BinX API

BinX is a secure convenience‑focused file storage service designed for simplicity and speed. Create password‑protected vaults to organize and safeguard your files. Access your vaults in two modes:

* **Owner**: Authenticate with both vault name and password to view, upload, delete, rename, and change visibility of all files (both `private` & `public`).
* **Guest**: Authenticate with vault name only to browse and download `public` files in read‑only mode.

With BinX, you can **create vaults**, **log in (as guest or owner)**, **upload files**, **download**, **delete**, **rename**, and **change file visibility**.

> Status: Active Development

Find the NextJS frontend repository [here](https://github.com/itsmmdoha/binx-frontend)

## 🛠️ Tech Stack

1. FastAPI (API)  
2. Pydantic (Data Validation and Serialization)  
3. PostgreSQL (Database)  
4. SQLAlchemy (ORM)  
5. S3‑compatible storage

## 📥 Getting Started

The BinX API depends on MinIO (for S3‑compatible storage) and PostgreSQL. A `docker-compose.yml` is provided to spin up these services:

```yaml
services:
  minio:
    image: minio/minio:latest
    container_name: minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    entrypoint: >
      /bin/sh -c "
      minio server --console-address ':9001' /data &
      sleep 5;
      until curl -s http://localhost:9000/minio/health/live; do sleep 1; done;
      mc alias set local http://localhost:9000 minioadmin minioadmin;
      mc mb local/binx || true;
      wait
      "

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
````

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

   Make sure you have Docker and Docker Compose installed and run:

   ```bash
   docker-compose up -d
   ```

   * MinIO available at [http://localhost:9000](http://localhost:9000)
   * PostgreSQL at `localhost:5432`
4. **Launch the API server**

   ```bash
   uvicorn app:app --reload
   ```
5. **Access API docs**

   * Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Documentation

Here's the [API Documentation](./API_Docs.md)

## ⚙️ Future Plans

* **Frontend**: Web UI for vault & file management.
* **Granular RBAC**: Roles beyond owner/guest (e.g., admin).
* **Audit Logging**: Track actions and access patterns.
* **Shareable Links**: Secure public file links with tokens.

## 🚀 Deployment

To deploy BinX in any environment (staging, production, etc.), simply provide the following environment variables. If you **do not** set them, BinX will fall back to the defaults defined in `config.py`—which match the development setup above:

| Variable         | Description                                     | Default (dev)                                            |
| ---------------- | ----------------------------------------------- | -------------------------------------------------------- |
| `FRONTEND_HOST`  | URL where the frontend is hosted                | `http://localhost:3000`                                  |
| `DATABASE_URL`   | SQLAlchemy‑style connection string for Postgres | `postgresql+psycopg://user:password@localhost:5432/binx` |
| `S3_ENDPOINT`    | S3‑compatible storage endpoint                  | `http://localhost:9000`                                  |
| `S3_ACCESS_KEY`  | S3/MinIO access key                             | `minioadmin`                                             |
| `S3_SECRET_KEY`  | S3/MinIO secret key                             | `minioadmin`                                             |
| `S3_BUCKET_NAME` | Default bucket name                             | `binx`                                                   |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens               | `your-secret-key`                                        |

You can export these in your shell or supply them via a `.env` file:

```bash
export DATABASE_URL="postgresql+psycopg://prod_user:prod_pass@db.example.com:5432/binx_prod"
export S3_ENDPOINT="https://s3.example.com"
export S3_ACCESS_KEY="PRODACCESSKEY"
export S3_SECRET_KEY="PRODSECRETKEY"
export S3_BUCKET_NAME="binx-production"
export JWT_SECRET_KEY="a-very-secure-secret"
```

Then start your service as usual:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

---

## 📄 License

Released under the MIT License. See [LICENSE](./LICENSE) for details.
