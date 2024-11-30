from typing import Optional
from datetime import date as datetime_date
from sqlalchemy import Column, Integer, String, Text, Date
from sqlalchemy.orm import registry, declarative_base
from sqlalchemy.orm import Mapped

# Create the registry
mapper_registry = registry()
Base = declarative_base()

class APODData(Base):
    __tablename__ = 'apod_data'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = Column(String(255))
    explanation: Mapped[str] = Column(Text)
    url: Mapped[str] = Column(Text)
    date: Mapped[datetime_date] = Column(Date)
    media_type: Mapped[str] = Column(String(50))

    def __repr__(self) -> str:
        return f"<APODData(title='{self.title}', date='{self.date}')>"