import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "mutual-fund-news-secret")
    NEWS_TOPIC = os.getenv("NEWS_TOPIC", "mutual fund india")
    NEWS_LIMIT = max(int(os.getenv("NEWS_LIMIT", 7)), 1)
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    NEWS_API_PROVIDER = os.getenv("NEWS_API_PROVIDER", "newsapi").lower()
    NEWS_LANGUAGE = os.getenv("NEWS_LANGUAGE", "en")
