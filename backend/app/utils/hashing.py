from passlib.context import CryptContext

# Create a CryptContext for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Hash:
    @staticmethod
    def bcrypt(password: str) -> str:
        """
        Hash the given plain text password using bcrypt.
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against the stored hashed password.
        """
        return pwd_context.verify(plain_password, hashed_password)
