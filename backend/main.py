from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
import auth
import servers
import uploads
import ai
import reputation
import blacklist
import bounty
import reports
import admin
import news

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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