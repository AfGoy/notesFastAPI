import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    URL = "http://127.0.0.1:8000"
    DB_URL = os.getenv("DB_URL")
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    MINUTES = 1
    REFRESH_TOKEN_DAYS = 7
    TOKEN_MIN_EXEPT = 1