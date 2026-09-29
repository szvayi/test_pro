from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
    """供部署平台进行存活和就绪检查。"""
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
