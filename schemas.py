"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Literal

# Existing examples left for reference
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Anime streaming app schemas

class Episode(BaseModel):
    number: int = Field(..., ge=1, description="Episode number")
    title: str = Field(..., description="Episode title")
    duration_minutes: int = Field(..., ge=1, le=300, description="Length in minutes")
    video_url: Optional[str] = Field(None, description="Streaming URL (demo)")

class Show(BaseModel):
    title: str
    description: str
    genres: List[str] = Field(default_factory=list)
    type: Literal["anime", "cartoon"] = Field("anime")
    year: Optional[int] = Field(None, ge=1900, le=2100)
    rating: Optional[float] = Field(None, ge=0, le=10)
    poster_url: Optional[HttpUrl] = None
    backdrop_url: Optional[HttpUrl] = None
    tags: List[str] = Field(default_factory=list)
    episodes: Optional[List[Episode]] = None

class WatchlistItem(BaseModel):
    user_id: str = Field(..., description="Anonymous or real user identifier")
    show_id: str = Field(..., description="Referenced show _id as string")

class UserProgress(BaseModel):
    user_id: str
    show_id: str
    episode_number: int
    position_seconds: int = Field(0, ge=0)
