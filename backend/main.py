from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from database import engine, Base
import models  # 触发所有模型注册

from routers import auth, subjects, records, mistakes, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 建表（开发阶段直接建，生产环境用 alembic）
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="AI学习助手 API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 生产环境改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 本地上传文件静态访问（OSS 上线后不需要）
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 注册路由
app.include_router(auth.router)
app.include_router(subjects.router)
app.include_router(records.router)
app.include_router(mistakes.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
