from fastapi import FastAPI, Depends, HTTPException, Response, Request
from pydantic import BaseModel

from dbm import Vault, File, get_session
from auth_helper import Password, Token


class VaultInfo(BaseModel):
    vault: str
    password: str

app = FastAPI()

@app.get("/")
def list_vaults(session = Depends(get_session)):
    return session.query(Vault).all()

@app.post("/vault/create")
def create_vault(vault_info: VaultInfo, db_session = Depends(get_session)):
    hashed_password = Password.generate_hash(vault_info.password)
    new_vault = Vault(vault=vault_info.vault, size=500, password_hash = hashed_password)
    db_session.add(new_vault)
    try:
        db_session.commit()
    except:
        raise HTTPException(status_code=409, detail=f"Vaultname: {vault_info.vault} already exists")
    return {"msg":"vault created successfully"}

@app.post("/vault/login")
def login(response: Response, vault_info: VaultInfo, db_session = Depends(get_session)):
    vault = db_session.query(Vault).filter(Vault.vault==vault_info.vault).first()
    if Password.is_valid(password=vault_info.password, hash_string=vault.password_hash):
        payload = {"vault":vault.vault}
        token = Token.generate(payload, valid_for=12*3600)  # valid for 1 hour

        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,  
            max_age=12*3600,   
            #secure=True,   
            samesite="lax"  
        )
        return "Login successful"
    else:
        return "Invalid Credentials"


