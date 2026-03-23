from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import user_router, clothes_router, outfit_router, outfit_history_router
from app.routers.chat import router as chat_router

app = FastAPI(
    title="AI 穿搭 Agent 系统",
    description="AI 穿搭推荐系统的 MVP 版本",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(clothes_router)
app.include_router(outfit_router)
app.include_router(outfit_history_router)
app.include_router(chat_router)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {"message": "AI 穿搭 Agent 系统 API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)