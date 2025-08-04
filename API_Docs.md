With BinX, you can **create Vaults**, **log in (as guest or owner)**, **upload files**, **download**, **delete**, **rename**, and **change their visibility**.

All API communication is done in `json` unless stated otherwise (e.g. file upload uses `multipart/form-data`). All authenticated routes require a **JWT Bearer token** in the header:

```
Authorization: Bearer <your_jwt_token>
```

---

## Table of Contents

1. [Vault Operations](#vault-operations)

   * [Create a Vault](#create-a-vault)
   * [Login to Vault](#login-to-vault)
   * [Fetch File List from Vault](#fetch-file-list-from-vault)
   * [Update a Vault](#update-a-vault)
   * [Delete a Vault](#delete-a-vault)

2. [File Operations](#file-operations)

   * [Upload a File](#upload-a-file)
   * [Download a File](#download-a-file)
   * [Delete a File](#delete-a-file)
   * [Bulk Delete Files](#bulk-delete-files)
   * [Update a File (Rename or Change Visibility)](#update-a-file-rename-or-change-visibility)
   * [Multipart Upload (Large Files)](#multipart-upload-large-files)


---

# 1. Vault Operations

## Create a Vault

**Endpoint:** `POST /vault/create`

Create a new vault by sending its name and a password.

### Request

```json
{
  "vault": "myvault",
  "password": "strongpassword"
}
```

### JS Fetch Example

```js
fetch("/vault/create", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ vault: "myvault", password: "strongpassword" })
})
```

### Response (200)

```json
{
  "message": "Vault created successfully."
}
```

### Response (409)

```json
{
  "detail": "Vault already exists."
}
```

---

## Login to Vault

**Endpoint:** `POST /vault/login`

Log in as **owner** (vault + password) or **guest** (vault only).

### Request (Owner)

```json
{
  "vault": "myvault",
  "password": "strongpassword"
}
```

### JS Fetch Example

```js
fetch("/vault/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ vault: "myvault", password: "strongpassword" })
})
```

### Response (200)

```json
{
  "message": "Login successful.",
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}
```

Subsequent requests require this token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

---

## Fetch File List from Vault

**Endpoint:** `GET /vault/fetch`

Returns vault metadata and file list.

### JS Fetch Example

```js
fetch("/vault/fetch", {
  headers: { Authorization: `Bearer ${token}` }
})
```

### Response

```json
{
  "vault": {
    "vault": "string",
    "date_created": "2025-07-09T08:09:33.421Z",
    "size": 0,
    "used_storage": 0
  },
  "files": [
    {
      "file": "string",
      "visibility": "private",
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "size": 0,
      "date_created": "2025-07-09T08:09:33.422Z"
    }
  ]
}
```

---

## Update a Vault

**Endpoint:** `PUT /vault`

Update vault properties: **rename** and/or **change password**. Both `new_name` and `new_password` are optional fields; at least one must be provided.

* To **rename** the vault, include the `new_name` field in the request body.
* To **change the password**, include the `new_password` field in the request body.
* To perform **both actions**, include both attributes in the same request.

### Request Body

```json
{
  "new_name": "renamedVault",
  "new_password": "newStrongPassword"
}
```

### JS Fetch Example

```js
fetch("/vault", {
  method: "PUT",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`
  },
  body: JSON.stringify({ new_name: "renamedVault", new_password: "newStrongPassword" })
})
```

### Response (200)

```json
{
  "message": "Vault Information Updated successfully"
}
```

### Error Responses

* **401 Unauthorized** – Not authorized (must be vault owner).
* **403 Forbidden** – Action forbidden.
* **404 Not Found** – Vault not found.

---

## Delete a Vault

**Endpoint:** `DELETE /vault`

Deletes the vault and all its files. Only the vault owner may perform this action.

### JS Fetch Example

```js
fetch("/vault", {
  method: "DELETE",
  headers: { Authorization: `Bearer ${token}` }
})
```

### Response (200)

```json
{
  "message": "Vault Deleted successfully"
}
```

### Error Responses

* **401 Unauthorized** – Not authorized (must be vault owner).
* **403 Forbidden** – Action forbidden.

---

# 2. File Operations

## Upload a File

**Endpoint:** `POST /file/upload`

Upload a file to the vault using multipart form.

### JS Fetch Example

```js
const formData = new FormData();
formData.append("file", selectedFile);

fetch("/file/upload", {
  method: "POST",
  headers: { Authorization: `Bearer ${token}` },
  body: formData
})
```

### Response

```json
{
  "message": "File uploaded successfully."
}
```

---

## Download a File

**Endpoint:** `GET /file/{file_id}`

Generates a temporary download URL.

### JS Fetch Example

```js
fetch(`/file/${fileId}`, {
  headers: { Authorization: `Bearer ${token}` }
})
```

### Response

```json
{
  "download_url": "https://binx.cdn.com/files/d7306...",
  "valid_for_seconds": 3600
}
```

---

## Delete a File

**Endpoint:** `DELETE /file/{file_id}`

Deletes a file from your vault.

### JS Fetch Example

```js
fetch(`/file/${fileId}`, {
  method: "DELETE",
  headers: { Authorization: `Bearer ${token}` }
})
```

### Response

```json
{
  "message": "File deleted successfully."
}
```

---

## Bulk Delete Files

**Endpoint:** `POST /file/bulk-delete`

Delete multiple files at once by providing a list of their `file_id`s.

### Request

```json
{
  "file_ids": [
    "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "b1a25f64-1234-4562-b3fc-2c963f66xyz1"
  ]
}
```

### JS Fetch Example

```js
fetch("/file/bulk-delete", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`
  },
  body: JSON.stringify({ file_ids: [
      "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "b1a25f64-1234-4562-b3fc-2c963f66xyz1"
    ]
  })
})
```

### Response

```json
{
  "deleted_files": {
    "count": 1,
    "file_ids": [
      "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    ]
  },
  "files_not_found": {
    "count": 1,
    "file_ids": [
      "b1a25f64-1234-4562-b3fc-2c963f66xyz1"
    ]
  }
}
```

---

## Update a File (Rename or Change Visibility)

**Endpoint:** `PUT /file/{file_id}`

Send either the `new_name` or `visibility` field to rename the file or change its visibility. You can also send both to update both attributes at once.

### Request

```json
{
  "new_name": "renamed_file.pdf",
  "visibility": "public"
}
```

### JS Fetch Example

```js
fetch(`/file/${fileId}`, {
  method: "PUT",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`
  },
  body: JSON.stringify({ new_name: "renamed_file.pdf", visibility: "public" })
})
```

### Response

```json
{
  "message": "File updated successfully."
}
```

Thanks! Based on both your FastAPI router implementation and the OpenAPI JSON, I’ve verified and refined the **Multipart Upload section** to fully align with the OpenAPI contract, schema references, error responses, required fields, and request types.

Below is the **Markdown section** you can insert into your existing `API_Docs.md`:

---

## Multipart Upload (Large Files)

Use multipart upload for large files (recommended for files over **20MB**). This approach breaks a file into smaller chunks, which are uploaded independently. Each chunk must be **at least 5MB** in size (except possibly the final one, if needed).

### Table of Steps

1. [Initiate Upload](#1-initiate-upload)
2. [Upload Chunks](#2-upload-chunks)
3. [Complete Upload](#3-complete-upload)
4. [Abort Upload (Optional)](#4-abort-upload)

All multipart operations require a **JWT Bearer Token** in the header:

```
Authorization: Bearer <your_jwt_token>
```

---

### 1. Initiate Upload

**Endpoint:** `POST /file/multipart/initiate`

Start a new multipart upload session. Send the full file name and its size in bytes.

#### Request (application/json)

```json
{
  "file_name": "example.mp4",
  "file_size": 17654967
}
```

#### Response (200)

```json
{
  "message": "Multipart upload initiated Successfully",
  "file_id": "06890cca-9bf5-79d8-8000-b1d9ad0670f9"
}
```

#### Errors

| Code | Description                 |
| ---- | --------------------------- |
| 401  | Unauthorized (JWT required) |
| 403  | Forbidden (must be owner)   |
| 507  | Insufficient Storage        |
| 500  | Internal Server Error       |
| 422  | Validation Error            |

---

### 2. Upload Chunks

**Endpoint:** `PUT /file/multipart/{file_id}/chunk`

Upload a chunk of the file using `multipart/form-data`.
Each part must have:

* `part_number`: integer (starting from 1)
* `chunk`: binary data (chunk)

#### Form Data Fields

| Field        | Type    | Required | Description                |
| ------------ | ------- | -------- | -------------------------- |
| part\_number | integer | ✅        | The index of this chunk    |
| chunk        | file    | ✅        | Binary data for this chunk |

Each chunk must be at least **5MB**. The part number must increment by one for each chunk (1, 2, 3, ...).

#### JS Fetch Example

```js
const formData = new FormData();
formData.append("part_number", 1);
formData.append("chunk", chunkBlob);

fetch(`/file/multipart/${fileId}/chunk`, {
  method: "PUT",
  headers: {
    Authorization: `Bearer ${token}`
  },
  body: formData
});
```

#### Response (200)

```json
{
  "message": "Chunk uploaded successfully"
}
```

#### Errors

| Code | Description                      |
| ---- | -------------------------------- |
| 400  | Chunk too small or invalid input |
| 401  | Unauthorized                     |
| 403  | Forbidden                        |
| 500  | Upload failed                    |
| 422  | Validation Error                 |

---

### 3. Complete Upload

**Endpoint:** `POST /file/multipart/{file_id}/complete`

Call this after all chunks have been successfully uploaded. The system will verify file size, compile the chunks, and store the final file.

#### JS Fetch Example

```js
fetch(`/file/multipart/${fileId}/complete`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`
  }
});
```

#### Response (200)

```json
{
  "message": "File uploaded successfully"
}
```

#### Errors

| Code | Description                            |
| ---- | -------------------------------------- |
| 400  | Chunk data is incomplete or mismatched |
| 401  | Unauthorized                           |
| 403  | Forbidden                              |
| 507  | Insufficient Storage                   |
| 500  | Completion failed                      |
| 422  | Validation Error                       |

---

### 4. Abort Upload (Optional)

**Endpoint:** `DELETE /file/multipart/{file_id}/abort`

If a multipart upload is interrupted or needs to be canceled, this will discard all uploaded parts.

#### Response (200)

```json
{
  "message": "multipart upload aborted"
}
```

#### Errors

| Code | Description            |
| ---- | ---------------------- |
| 404  | Upload not found       |
| 401  | Unauthorized           |
| 403  | Forbidden              |
| 500  | Abort operation failed |
| 422  | Validation Error       |

---

### Notes

* You must **initiate** before uploading chunks.
* Only use this flow for files over **20MB**. For smaller files, use `/file/upload`.
* Chunks must be uploaded **in order** using increasing `part_number`.
* Each chunk must be **≥ 5MB**, except possibly the final one.
* Use the `file_id` from step 1 in all other steps.

---

Let me know if you’d like me to patch this section into the actual file or export the modified `.md` for you.


---

## Notes

* `file_id` is returned from `/vault/fetch` and used in all file operations.
* Visibility can be `"public"` or `"private"`.
* JWT tokens expire — refresh via login if needed.

BinX is secure by design. You define access and keep control.
