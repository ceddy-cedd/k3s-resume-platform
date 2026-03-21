from fastapi import FastAPI
import feedparser

app = FastAPI()

RSS_FEEDS = [
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml"
]

@app.get("/")
def read_root():
    return {"message": "Tech RSS Aggregator"}

@app.get("/news")
def get_news():
    articles = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:5]:
            articles.append({
                "title": entry.title,
                "link": entry.link
            })

    return {"articles": articles}