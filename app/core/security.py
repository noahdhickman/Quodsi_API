def get_password_hash(password: str) -> str:
    return "hashed_" + password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashed_password == "hashed_" + plain_password
