from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
import base64

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

from config import settings
from db.redis import get_redis_connection

class AESMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.headers.get("X-ENFORCE-AES256") != "1":
            return await call_next(request)

        try:
            auth_header = request.headers.get("Authorization", "")
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            jti = payload.get("jti")
            if not jti:
                return JSONResponse(status_code=401, content={"detail": "Token missing JTI"})
        except (JWTError, IndexError):
            return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

        redis_client = get_redis_connection()
        key_b64 = redis_client.get(f"session_key:{jti}")
        
        if not key_b64:
            return JSONResponse(status_code=401, content={"detail": "Invalid session key. Please log in again."})
        
        aes_key = base64.b64decode(key_b64)
        
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    encrypted_body = base64.b64decode(body)
                    iv = encrypted_body[:16]
                    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
                    decrypted_body = unpad(cipher.decrypt(encrypted_body[16:]), AES.block_size)
                    
                    async def receive():
                        return {"type": "http.request", "body": decrypted_body, "more_body": False}
                    request = Request(request.scope, receive)
            except Exception:
                return JSONResponse(status_code=400, content={"detail": "Invalid AES encrypted data"})

        response = await call_next(request)

        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        if response_body and response.headers.get('content-type') == 'application/json':
            iv = get_random_bytes(16)
            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            padded_data = pad(response_body, AES.block_size)
            encrypted_response_body = iv + cipher.encrypt(padded_data)
            
            return JSONResponse(
                content=base64.b64encode(encrypted_response_body).decode('utf-8'),
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        return response