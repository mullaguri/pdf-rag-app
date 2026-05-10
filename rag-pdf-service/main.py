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
    # Check vector store dimension compatibility
    try:
        from vectorstore.pinecone_store import get_vectorstore
        vectorstore = get_vectorstore()
        if vectorstore:
            print(f"✅ Vector store initialized successfully with dimension: {vectorstore.embedding_dimension}")
    except ValueError as e:
        if "Dimension mismatch" in str(e):
            print(f"❌ Startup failed: {e}")
            print("🛑 Application cannot start with dimension mismatch.")
            print("Solution: Either delete the Pinecone index or update EMBEDDING_MODEL/EMBEDDING_DIMENSION in .env")
            raise SystemExit(1)  # Force application to exit
        raise
    except Exception as e:
        print(f"⚠️ Vector store initialization warning: {e}")

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