import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-only-change-me"
    )

    # Read the database URL from the environment.
    database_url = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/disaster_management"
    )

    # Railway commonly provides MySQL URLs beginning with mysql://.
    # Our project uses PyMySQL, so convert the driver automatically.
    if database_url.startswith("mysql://"):
        database_url = database_url.replace(
            "mysql://",
            "mysql+pymysql://",
            1
        )

    SQLALCHEMY_DATABASE_URI = database_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }


class TestConfig(Config):
    TESTING = True

    SECRET_KEY = "test-secret"

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "sqlite:///:memory:"
    )