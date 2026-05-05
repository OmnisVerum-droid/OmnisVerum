import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import admin
import ai
import auth
import blacklist
import bounty
import news
import reputation
import reports
import servers
import uploads
from database import Base, engine
from middleware import ErrorHandlingMiddleware, RateLimitMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()

_cors = os.getenv("OMNISVERUM_CORS_ORIGINS", "").strip()
if _cors:
    _allow_origins = [o.strip() for o in _cors.split(",") if o.strip()]
    _allow_credentials = True
else:
    _allow_origins = ["*"]
    _allow_credentials = False

# Add middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(servers.router)
app.include_router(uploads.router)
app.include_router(ai.router)
app.include_router(reputation.router)
app.include_router(blacklist.router)
app.include_router(bounty.router)
app.include_router(reports.router)
app.include_router(admin.router)
app.include_router(news.router)

@app.get("/")
def read_root():
    return {"message": "Omnisverum is alive"}