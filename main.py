from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from database import check_database_connection

load_dotenv()
app = FastAPI(
    title="Test Pro API",
    description="用于前端欢迎页演示的 FastAPI 服务",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["系统"])
def health_check() -> dict[str, str]:
    """返回服务当前是否可用。"""
    return {"status": "ok", "message": "服务运行正常"}


@app.get("/healthz", tags=["系统"])
def healthz() -> dict[str, str]:
    """供部署平台进行存活检查，不依赖数据库。"""
    return {"status": "ok"}


@app.get("/readyz", tags=["系统"])
async def readyz() -> dict[str, str]:
    """供部署平台进行就绪检查，并验证数据库连通性。"""
    if not await check_database_connection():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready",
        )
    return {"status": "ok"}


@app.get("/api/routes", tags=["系统"])
def api_routes() -> dict[str, object]:
    """返回前端需要展示的 API 列表。"""
    return {
        "items": [
            {
                "method": "GET",
                "path": "/api/health",
                "name": "健康检查",
                "description": "检查 API 服务是否正常运行",
            },
            {
                "method": "GET",
                "path": "/api/routes",
                "name": "API 接口列表",
                "description": "获取当前服务提供的接口列表",
            },
            {
                "method": "GET",
                "path": "/readyz",
                "name": "就绪检查",
                "description": "检查服务和数据库是否已经准备好",
            },
        ]
    }


# 生产镜像会在构建阶段生成 web/dist；check_dir=False 允许本地只启动 API 时
# 暂未构建前端资源，部署后仍由该目录提供 Vue 页面和静态资源。
app.mount(
    "/",
    StaticFiles(directory="web/dist", html=True, check_dir=False),
    name="web",
)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

#
# kubectl create secret generic test-pro-backend-runtime
#   --from-env-file=.env
#   --namespace=vy-apps
#   --dry-run=client
#   -o yaml |
# kubectl apply -f -