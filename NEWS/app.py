from datetime import datetime

from flask import Flask, render_template

from config import Config
from services.news_service import NewsService

app = Flask(__name__)
app.config.from_object(Config)

news_service = NewsService(
    topic=app.config["NEWS_TOPIC"],
    page_size=app.config["NEWS_LIMIT"],
    api_key=app.config["NEWS_API_KEY"],
    api_provider=app.config["NEWS_API_PROVIDER"],
    language=app.config["NEWS_LANGUAGE"],
)


@app.route("/")
def index():
    categories = news_service.get_news_by_category()
    default_category = next(
        (name for name, items in categories.items() if items),
        next(iter(categories.keys()), "Large Cap"),
    )
    default_articles = categories.get(default_category, [])
    featured_article = default_articles[0] if default_articles else {
        "title": f"{default_category} mutual fund updates",
        "summary": "Live mutual-fund headlines will appear here when relevant stories are available.",
        "link": "#",
    }
    total_articles = sum(len(items) for items in categories.values())

    return render_template(
        "index.html",
        categories=categories,
        default_category=default_category,
        featured_article=featured_article,
        total_articles=total_articles,
        status_message=news_service.status_message,
        refreshed_at=datetime.now().strftime("%d %b %Y, %I:%M %p"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
