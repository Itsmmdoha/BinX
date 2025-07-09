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

---

## Notes

* `file_id` is returned from `/vault/fetch` and used in all file operations.
* Visibility can be `"public"` or `"private"`.
* JWT tokens expire — refresh via login if needed.

BinX is secure by design. You define access and keep control.
