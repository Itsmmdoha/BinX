With BinX, you can **create Vaults**, **log in (as guest or owner)**, **upload files**, **download**, **delete**, **rename**, and **change their visibility**.

All API communication is done in `json` unless stated otherwise (e.g. file upload uses `multipart/form-data`). All authenticated routes require a **JWT Bearer token** in the header:

```
Authorization: Bearer <your_jwt_token>
```

---

## Table of Contents

1. [Vault Operations](#vault-operations)

   - [Create a Vault](#create-a-vault)
   - [Login to Vault](#login-to-vault)
   - [Fetch File List from Vault](#fetch-file-list-from-vault)
2. [File Operations](#file-operations)

   - [Upload a File](#upload-a-file)
   - [Download a File](#download-a-file)
   - [Delete a File](#delete-a-file)
   - [Update a File (Rename or Change Visibility)](#update-a-file-rename-or-change-visibility)

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

The subsequent requests require you to send this token in the Authorization header like the following:

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
    "vault": "myvault",
    "date_created": "2025-06-14T12:00:00",
    "size": 1000000000,
    "used_storage": 2345678
  },
  "files": [
    {
      "file": "report.pdf",
      "file_id": "d73061f0-a1b4-4d63-b0ed-4f7f67f1a6d5",
      "size": 123456,
      "visibility": "private",
      "date_created": "2025-06-13T15:30:00"
    }
  ]
}
```

Each file has a `file_id`; this id is used to perform file operations on files.

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

---

## Notes

* `file_id` is returned from `/vault/fetch` and used in all file operations.
* Visibility can be `"public"` or `"private"`.
* JWT tokens expire — refresh via login if needed.

BinX is secure by design. You define access and keep control.
