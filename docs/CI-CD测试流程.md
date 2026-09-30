# test_pro CI/CD 测试流程

本项目采用两套 Kubernetes 环境：Release 正式环境和 Pull Request 临时测试环境。两套环境都通过 SWR、Kestra 和公共 Helm Chart 完成部署。

## Workflow

| Workflow | 触发 | 作用 | 是否部署 |
| --- | --- | --- | --- |
| `ci.yml` | PR、main/master push | 后端 smoke、前端 build、Docker build | 否 |
| `pr-deploy.yml` | PR opened、reopened、synchronize、closed | 构建 PR 镜像、部署/清理 Kubernetes 临时环境 | 是，PR 测试环境 |
| `deploy.yml` | Release published、手动 | 构建 Release 镜像、触发正式 Kubernetes 部署 | 是，正式环境 |
| `build-test-image.yml` | 手动 | 旧的 Docker 测试镜像构建流程 | 兼容保留，不是主流程 |
| `deploy-test.yml` | 手动 | 旧的 Docker 主机部署流程 | 兼容保留，不是主流程 |

`build-test-image.yml` 和 `deploy-test.yml` 仍存在于仓库，但当前主测试部署路径是 `pr-deploy.yml`，不再依赖 SSH 到 Docker 测试主机。

## PR Kubernetes 测试环境

`pr-deploy.yml` 对同一个 PR 使用固定的临时资源：

```text
PR #123
  Release:   test-pro-pr-123
  Namespace: vayi-pr-123
  Host:      test-pro-pr-123.app.vayi.cn
  Image tag: pr-123-<commit-sha>
```

PR 打开、重新打开或有新提交时，Workflow 会：

1. 校验 `.deploy/deploy.json`；
2. 根据 `services` 并行构建并推送镜像；
3. 根据 PR 编号生成 Release、Namespace 和域名；
4. 将 `services` 和 `jobs` 生成 Kestra payload；
5. 调用统一 `KESTRA_WEBHOOK_URL`；
6. 等待 Kestra/Helm 部署完成；
7. 验收首页、`/healthz`、`/api/health` 和 `/api/routes`。

PR 关闭时会调用同一个 Kestra Webhook 的清理操作，等待清理执行成功后结束 Workflow。

PR fork 不会执行带 Secrets 的镜像构建、部署和清理 Job；fork PR 只执行普通 CI。

## Release 正式环境

`deploy.yml` 监听 GitHub Release Published，也支持手动触发：

```text
Release published
  ↓
校验 deploy.json
  ↓
根据 services 构建并推送 Release 镜像
  ↓
生成 deploy-payload.json
  ↓
调用 Kestra 正式部署 Flow
  ↓
等待 Helm/Kubernetes 完成
  ↓
验收正式域名
```

正式环境使用 `.deploy/deploy.json` 中的：

```text
projectName: test-pro
host: test-pro.app.vayi.cn
```

正式 Workflow 当前不使用 GitHub Environment，正式凭证应配置为仓库级或组织级 Secrets。

## Secrets

统一需要：

```text
SWR_USERNAME
SWR_PASSWORD
KESTRA_WEBHOOK_URL
KESTRA_USER
KESTRA_PASSWORD
```

PR Workflow 的构建和部署 Job 当前使用 GitHub Environment `test`；正式 Workflow 不使用 Environment。禁止将这些凭证写入仓库文件、镜像或 `deploy-payload.json`。

## `deploy.json` 与一次性 Job

服务定义位于：

```text
.deploy/deploy.json
```

每个服务需要提供：

```text
name
context
dockerfile
image
containerPort
servicePort
expose
```

`jobs` 用于数据库迁移和初始化任务。当前项目的配置是一个安全模拟 Job，执行内存 SQLite 的 `SELECT 1`，不会连接或修改外部数据库：

```json
{
  "name": "migrate",
  "image": "test-pro",
  "command": ["python", "-c"],
  "args": ["import sqlite3; connection = sqlite3.connect(':memory:'); connection.execute('SELECT 1'); print('migration check: SELECT 1 OK'); connection.close()"],
  "backoffLimit": 1,
  "ttlSecondsAfterFinished": 300
}
```

正式接入数据库时，应替换为真实迁移命令并通过 Kubernetes Secret 注入数据库配置。迁移 Job 失败时，Helm 使用 `--wait-for-jobs` 使整个部署失败。

## 推荐执行顺序

1. 提交 PR，确认 `ci.yml` 通过；
2. `pr-deploy.yml` 自动构建 PR 镜像并部署独立 Kubernetes 环境；
3. 访问 PR 独立域名，验收首页和 API；
4. PR 关闭后确认 Kestra 清理任务成功；
5. 合并后创建并发布 GitHub Release；
6. `deploy.yml` 构建 Release 镜像并部署正式环境；
7. 验收正式域名和健康检查。
