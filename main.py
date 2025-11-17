import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Show, WatchlistItem, UserProgress

app = FastAPI(title="AniFlix API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AniFlix backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Utility to convert Mongo documents to JSON-friendly dicts

def serialize_doc(doc):
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    return d

# Seed demo shows if empty
@app.post("/seed", tags=["admin"])
async def seed_demo():
    count = db["show"].count_documents({}) if db else 0
    if count > 0:
        return {"seeded": False, "count": count}
    demos = [
        {
            "title": "Attack on Titan",
            "description": "Humans vs. titans in a walled world.",
            "genres": ["action", "drama"],
            "type": "anime",
            "year": 2013,
            "rating": 9.0,
            "poster_url": "https://image.tmdb.org/t/p/w342/aiy35Evcofzl7hASZZvsFgltHTX.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/gnWgk6W2vNhbbX6YsJhBKt3vnDn.jpg",
            "tags": ["trending", "popular"],
        },
        {
            "title": "Demon Slayer",
            "description": "Tanjiro becomes a demon slayer after tragedy.",
            "genres": ["action", "fantasy"],
            "type": "anime",
            "year": 2019,
            "rating": 8.8,
            "poster_url": "https://image.tmdb.org/t/p/w342/wrCVHdkBlBWdJUZPvnJWcBRuhSY.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/bOGk3ZcZ1UBX8ZUBKbjDg7sWXBm.jpg",
            "tags": ["trending"],
        },
        {
            "title": "Avatar: The Last Airbender",
            "description": "The four nations, one avatar.",
            "genres": ["adventure", "fantasy"],
            "type": "cartoon",
            "year": 2005,
            "rating": 9.2,
            "poster_url": "https://image.tmdb.org/t/p/w342/cs0neU42Pvvrg1I8o1gChX2NDSS.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/8mRgpubxHqnqvENK3H4WlfHXo60.jpg",
            "tags": ["classic"],
        },
    ]
    for d in demos:
        create_document("show", d)
    return {"seeded": True, "count": len(demos)}

# Shows endpoints
@app.get("/shows", response_model=list)
async def list_shows(
    q: Optional[str] = Query(None, description="search query"),
    genre: Optional[str] = None,
    type: Optional[str] = Query(None, pattern="^(anime|cartoon)$"),
    tag: Optional[str] = None,
    limit: int = 50,
):
    if db is None:
        raise HTTPException(500, "Database not configured")
    filt = {}
    if q:
        filt["title"] = {"$regex": q, "$options": "i"}
    if genre:
        filt["genres"] = genre
    if type:
        filt["type"] = type
    if tag:
        filt["tags"] = tag
    docs = db["show"].find(filt).limit(limit)
    return [serialize_doc(d) for d in docs]

@app.post("/shows", status_code=201)
async def create_show(show: Show):
    if db is None:
        raise HTTPException(500, "Database not configured")
    _id = create_document("show", show)
    return {"_id": _id}

@app.get("/shows/{show_id}")
async def get_show(show_id: str):
    if db is None:
        raise HTTPException(500, "Database not configured")
    try:
        doc = db["show"].find_one({"_id": ObjectId(show_id)})
    except Exception:
        raise HTTPException(400, "Invalid id")
    if not doc:
        raise HTTPException(404, "Not found")
    return serialize_doc(doc)

# Watchlist endpoints
@app.post("/watchlist", status_code=201)
async def add_watchlist(item: WatchlistItem):
    if db is None:
        raise HTTPException(500, "Database not configured")
    _id = create_document("watchlistitem", item)
    return {"_id": _id}

@app.get("/watchlist")
async def get_watchlist(user_id: str):
    if db is None:
        raise HTTPException(500, "Database not configured")
    items = db["watchlistitem"].find({"user_id": user_id})
    # Join with shows
    show_ids = [ObjectId(i["show_id"]) for i in items if ObjectId.is_valid(i.get("show_id", ""))]
    shows = list(db["show"].find({"_id": {"$in": show_ids}})) if show_ids else []
    return [serialize_doc(s) for s in shows]

# Progress endpoints
@app.post("/progress", status_code=201)
async def set_progress(p: UserProgress):
    if db is None:
        raise HTTPException(500, "Database not configured")
    db["userprogress"].update_one(
        {"user_id": p.user_id, "show_id": p.show_id},
        {"$set": p.model_dump()},
        upsert=True,
    )
    return {"ok": True}

@app.get("/progress")
async def get_progress(user_id: str, show_id: str):
    if db is None:
        raise HTTPException(500, "Database not configured")
    doc = db["userprogress"].find_one({"user_id": user_id, "show_id": show_id})
    return serialize_doc(doc) if doc else {}

# Simple schema endpoint for viewers
@app.get("/schema")
async def get_schema():
    return {
        "collections": [
            "show",
            "watchlistitem",
            "userprogress",
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
