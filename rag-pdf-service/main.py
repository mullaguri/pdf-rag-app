from fastapi import FastAPI
from database import create_tables
from routers import ingest_router, rag_router, auth
from fastapi.middleware.cors import CORSMiddleware
from routers.auth import oauth2_bearer
import models
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="PDF RAG Service",
    description="Upload PDFs → Create Embeddings → Ask Questions via LLM",
    version="1.0.0"
)

app.include_router(ingest_router.router)
app.include_router(rag_router.router)
app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "PDF RAG Service is running. Visit /docs for API reference."}

@app.on_event("startup")
def on_startup():
    create_tables()

@app.get("/routes")
def get_all_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else []
        })
    return routes