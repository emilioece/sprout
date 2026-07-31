from passlib.context import CryptContext

# Uses pbkdf2_sha256 instead of bcrypt — same security goal (safely
# hashing passwords), but avoids needing a C compiler on Windows.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)