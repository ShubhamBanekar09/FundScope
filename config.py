import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "mutual-fund-integration-secret-key-123")
    NEWS_TOPIC = os.getenv("NEWS_TOPIC", "mutual fund india")
    NEWS_LIMIT = max(int(os.getenv("NEWS_LIMIT", 7)), 1)
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    NEWS_API_PROVIDER = os.getenv("NEWS_API_PROVIDER", "newsapi").lower()
    NEWS_LANGUAGE = os.getenv("NEWS_LANGUAGE", "en")


# This creates a file named fundscope.db in your app's root folder
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fundscope.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False