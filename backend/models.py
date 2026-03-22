from pydantic import BaseModel
from typing import List, Optional


class EventResponse(BaseModel):
    id: int
    title: str
    venue: Optional[str] = None
    date: Optional[str] = None
    genres: List[str] = []
    city: str = "Istanbul"
    ticket_url: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None
    liked: bool = False


class UserCreate(BaseModel):
    username: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: Optional[str] = None


class ScraperLog(BaseModel):
    id: int
    source: str
    status: str
    message: Optional[str] = None
    events_found: int = 0
    created_at: Optional[str] = None
