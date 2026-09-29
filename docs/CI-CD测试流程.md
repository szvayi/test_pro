# test_pro CI/CD 测试流程

本项目用于先验证统一 CI/CD 的最小形态，再迁移到 POM 等多服务项目。

## Workflow

| Workflow | 触发 | 作用 | 是否部署 |
| --- | --- | --- | --- |
| `ci.yml` | PR、main/master push | 后端 smoke、前端 build、Docker build | 否 |
| `build-test-image.yml` | 手动 | 将指定 ref 构建并推送到 SWR 临时/测试 tag | 否 |
| `deploy-test.yml` | 手动 | 部署已有镜像到隔离测试环境并执行 smoke | 是，仅测试环境 |
| `deploy.yml` | Release、手动 | 现有生产式发布链路 | 是，生产流程 |

## 测试环境前置条件

运行 `deploy-test.yml` 前必须由基础设施负责人确认：

- `test-pro-test` 对应的 Kubernetes namespace 或 Kestra 项目标识；
- `test-pro-test.app.vayi.cn` 已配置 DNS、Ingress 和 HTTPS；
- 测试环境使用隔离数据库/配置，不连接生产数据；
- Kestra 能访问 SWR，并能将镜像部署到测试 namespace；
- GitHub Environment `test` 的审批策略和 secrets 已配置。

当前只提交 workflow，不自动触发测试环境部署。

## Secrets

建议将以下变量配置在仓库或 `test` Environment，禁止写入代码：

- `SWR_USERNAME` / `SWR_PASSWORD`
- `KESTRA_WEBHOOK_URL`
- `KESTRA_USER` / `KESTRA_PASSWORD`

PR CI 不需要这些 secrets，来自 fork 的 PR 也不应获得它们。

## 推荐执行顺序

1. PR 打开或更新，确认 `ci.yml` 的三个 job 通过；
2. 手动运行 `Build Test Image`，填写源 ref 和不可变 `image_tag`；
3. 确认 SWR 中镜像存在后，手动运行 `Deploy Test Environment`；
4. 填写同一个 `image_tag`、测试 project name 和测试 host；
5. 核对 Kestra 终态，以及 `/healthz`、`/api/health`、`/api/routes`；
6. 通过后再将 workflow 结构抽成多项目 reusable workflow。

生产 `deploy.yml` 暂不改动，避免测试方案未经验证就改变生产发布链路。
