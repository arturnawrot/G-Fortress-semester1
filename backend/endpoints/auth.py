from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import base64

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from redis import Redis

from db.models import User
from db.redis import get_redis_connection
from schemas.user import UserLogin, UserCreate
from schemas.token import Token
from security.hashing import verify_password, get_password_hash
from security.auth import create_access_token
from config import settings
from jose import jwt

router = APIRouter()

class SecureLoginRequest(UserLogin):
    client_public_key: str = Field(..., description="Base64 encoded client public key")

class SecureTokenResponse(Token):
    server_public_key: str = Field(..., description="Base64 encoded server public key")

@router.post("/login", response_model=SecureTokenResponse)
async def secure_login(form_data: SecureLoginRequest, redis_client: Redis = Depends(get_redis_connection)):
    user = User.match(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    server_private_key = x25519.X25519PrivateKey.generate()
    server_public_key = server_private_key.public_key()

    try:
        client_public_key_bytes = base64.b64decode(form_data.client_public_key)
        client_public_key = x25519.X25519PublicKey.from_public_bytes(client_public_key_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid client public key format")

    shared_secret = server_private_key.exchange(client_public_key)

    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'aes-session-key')
    aes_session_key = hkdf.derive(shared_secret)
    
    access_token = create_access_token(data={"sub": user.username})
    
    # Decode the token just created to get its unique ID (jti)
    token_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    jti = token_payload['jti']
    
    # Store the AES session key in Redis using the JTI as the key
    # It will expire at the same time as the JWT
    redis_client.set(f"session_key:{jti}", base64.b64encode(aes_session_key).decode('utf-8'), ex=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    # Prepare Response
    server_public_key_b64 = base64.b64encode(
        server_public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    ).decode('utf-8')

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "server_public_key": server_public_key_b64
    }