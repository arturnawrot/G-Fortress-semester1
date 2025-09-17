from Cryptodome.Hash import MD4

def ntlm_hash(password: str) -> str:
    return MD4.new(password.encode("utf-16le")).hexdigest()
