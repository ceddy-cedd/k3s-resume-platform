from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class FeedItem(Base):
    __tablename__ = "feed_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    source = Column(String(120), nullable=False)
    category = Column(String(80), nullable=False)
    summary = Column(Text, nullable=False)
    link = Column(String(1000), nullable=False, unique=True, index=True)
    published_at = Column(String(120), nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow)