import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken

##################################################################
class SettingsService:
    """
    Centralized configuration manager with encryption and environment switching.
    """

    # ----------------------------------------------------------
    def __init__(self, env: str = "dev", password: str | None = None):
        # Example: .env.dev, .env.prod
        self.env_file = f".env.{env}"
        self.enc_file = f"{self.env_file}.enc"
        self.key_file = ".env.key"
        self._cache = {}
        self.password = password

        if os.path.exists(self.env_file):
            self.load_env()
        elif os.path.exists(self.enc_file) and password:
            self.decrypt_env(password)
            self.load_env()
        else:
            raise FileNotFoundError("No .env or encrypted .env file found.")

    # ----------------------------------------------------------
    # Environment loading
    def load_env(self):
        load_dotenv(self.env_file)

    # ----------------------------------------------------------
    # Encryption utilities
    @staticmethod
    def _write_file(path, data):
        with open(path, "wb") as f:
            f.write(data)

    @staticmethod
    def _read_file(path):
        with open(path, "rb") as f:
            return f.read()

    def generate_key(self, password: str):
        key = Fernet.generate_key()
        with open(self.key_file, "wb") as f:
            f.write(key)
        print(f"Key file generated at {self.key_file}")
        return key

    def get_key(self):
        if not os.path.exists(self.key_file):
            raise FileNotFoundError("Encryption key not found. Generate one first.")
        return self._read_file(self.key_file)

    def encrypt_env(self):
        if not os.path.exists(self.env_file):
            raise FileNotFoundError(f"{self.env_file} not found.")
        key = self.get_key()
        f = Fernet(key)
        data = self._read_file(self.env_file)
        enc_data = f.encrypt(data)
        self._write_file(self.enc_file, enc_data)
        print(f"Encrypted config -> {self.enc_file}")

    def decrypt_env(self, password: str):
        key = self.get_key()
        f = Fernet(key)
        data = self._read_file(self.enc_file)
        try:
            dec_data = f.decrypt(data)
            with open(self.env_file, "wb") as f_out:
                f_out.write(dec_data)
            print(f"Decrypted env file -> {self.env_file}")
        except InvalidToken:
            raise ValueError("Invalid password or corrupted key")

    # ----------------------------------------------------------
    # Value accessors
    def get(self, key: str, default=None):
        if key in self._cache:
            return self._cache[key]
        value = os.getenv(key, default)
        self._cache[key] = value
        return value

    @property
    def openai_key(self): return self.get("OPENAI_API_KEY")
    @property
    def google_key(self): return self.get("GOOGLE_API_KEY")
    @property
    def deepseek_key(self): return self.get("DEEPSEEK_API_KEY")
    @property
    def lmstudio_url(self): return self.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
    @property
    def admin_password(self): return self.get("CONFIG_PASSWORD")
    
    # ----------------------------------------------------------

##################################################################
