# Test Pro

## 部署服务清单

项目通过 `.deploy/deploy.json` 描述部署信息。GitHub Actions 会读取这份文件，用它完成镜像构建参数生成、镜像命名和 Kubernetes 部署参数生成。

当前项目采用单镜像部署：Vue 3 在镜像构建阶段生成 `web/dist`，FastAPI 在 `8000` 端口同时提供 API 和前端静态页面。

```text
浏览器 -> https://test-pro.app.vayi.cn/
                      |
                      v
              test-pro:8000
                ├── /              Vue 页面
                ├── /healthz       存活/就绪检查
                ├── /api/health    API 健康检查
                └── /api/routes    API 接口列表
```

### 文件位置

```text
.deploy/
├── deploy.json         # 项目部署服务清单
└── deploy.schema.json  # 部署清单格式校验
```

### 当前配置

```json
{
  "projectName": "test-pro",
  "host": "test-pro.app.vayi.cn",
  "services": [
    {
      "name": "app",
      "context": ".",
      "dockerfile": "Dockerfile",
      "image": "test-pro",
      "containerPort": 8000,
      "servicePort": 8000,
      "path": "/",
      "expose": true
    }
  ]
}
```

### 字段说明

| 字段 | 说明 |
| --- | --- |
| `projectName` | 项目名称，使用小写字母、数字和短横线，并且需要唯一 |
| `host` | 正式访问域名，必须使用 `*.app.vayi.cn` 域名 |
| `services` | 项目中的全部部署服务，至少包含一个服务 |
| `name` | 服务名称，在当前项目内必须唯一 |
| `context` | Docker 构建上下文，相对于仓库根目录 |
| `dockerfile` | Dockerfile 路径，相对于仓库根目录 |
| `image` | 镜像名称，不填写仓库地址和版本 tag |
| `containerPort` | 容器实际监听端口 |
| `servicePort` | Kubernetes Service 端口 |
| `path` | 公网访问路径，例如 `/` 或 `/api` |
| `expose` | 是否通过公网入口暴露；为 `true` 时必须填写 `path` |
| `env` | 可选的普通运行时环境变量 |
| `envFrom` | 可选的 Kubernetes Secret 或 ConfigMap 引用 |

`image` 只填写镜像名，例如：

```text
test-pro
```

### 一次性任务和数据库迁移

`jobs` 用于数据库迁移、初始化数据等一次性任务。当前项目没有数据库迁移依赖，因此默认保持为空：

```json
"jobs": []
```

当镜像中加入迁移命令和数据库依赖后，可以按以下方式配置迁移任务。迁移任务通常复用应用服务镜像，并通过 Kubernetes Secret 注入数据库连接信息：

```json
"jobs": [
  {
    "name": "migrate",
    "image": "test-pro",
    "command": ["python", "-m", "your_migration_command"],
    "envFrom": [
      {
        "secretRef": {
          "name": "test-pro-runtime"
        }
      }
    ],
    "backoffLimit": 1,
    "ttlSecondsAfterFinished": 300
  }
]
```

PR 和 Release Workflow 会将 `jobs[].image` 转换为当前版本的完整镜像地址和 tag，并由部署平台使用 `--wait-for-jobs` 等待任务成功。不要在没有实际迁移命令或数据库 Secret 的情况下启用该任务。

镜像仓库地址由 Workflow 的 `REGISTRY` 和 `IMAGE_NAMESPACE` 统一拼接，镜像 tag 使用 Release tag 或 commit SHA 自动生成，不在 `deploy.json` 中维护。

### 发布流程

生产 Workflow 位于 `.github/workflows/deploy.yml`，发布流程如下：

```text
校验 deploy.json
    ↓
读取 services 生成构建矩阵
    ↓
构建并推送所有服务镜像
    ↓
根据 deploy.json 生成 Kestra payload
    ↓
部署到 Kubernetes
    ↓
验收首页、healthz 和 API
```

新增或调整服务时，优先修改 `.deploy/deploy.json`，并同步准备对应的 Dockerfile 和构建上下文。不要把数据库密码、Token、Webhook 或其他敏感信息写入该文件；运行时敏感配置应通过部署平台的 Kubernetes Secret 注入。

部署清单会在 Workflow 中使用 `.deploy/deploy.schema.json` 进行格式校验。校验失败时不会继续构建镜像或触发部署。

## 数据库配置

后端使用异步 SQLAlchemy 和 `asyncpg` 连接 PostgreSQL。部署时通过 Kubernetes Secret `test-pro-app-runtime` 注入数据库连接串，Secret 中应包含：

```text
DATADASE_URL=postgresql+asyncpg://用户名:密码@数据库地址:5432/数据库名
```

代码也兼容标准拼写 `DATABASE_URL`，但部署规范当前以 `DATADASE_URL` 为主。数据库连接串只在运行时注入，不写入 Git、Dockerfile、前端构建参数或镜像。

健康检查接口的区别：

```text
/healthz  进程存活检查，不依赖数据库
/readyz   就绪检查，需要数据库连接成功
```

当前只增加数据库连接和连通性检查，尚未创建业务表，也不会在容器启动时自动执行数据库迁移。

本地使用 `.env` 时，可通过 Uvicorn 加载环境变量：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --env-file .env
```

`.env` 只用于本地开发，生产环境应由 Kubernetes Secret `test-pro-app-runtime` 注入 `DATADASE_URL`。
