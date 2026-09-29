# test_pro CI/CD 测试流程

本项目用于先验证统一 CI/CD 的最小形态，再迁移到 POM 等多服务项目。

## Workflow

| Workflow | 触发 | 作用 | 是否部署 |
| --- | --- | --- | --- |
| `ci.yml` | PR、main/master push | 后端 smoke、前端 build、Docker build | 否 |
| `build-test-image.yml` | 手动 | 将指定 ref 构建并推送到 SWR 临时/测试 tag | 否 |
| `deploy-test.yml` | 手动 | SSH 到测试主机，用 Docker 运行已有镜像并执行 smoke | 是，仅测试环境 |
| `deploy.yml` | Release、手动 | 现有生产式发布链路 | 是，生产流程 |

## Docker 测试环境前置条件

运行 `deploy-test.yml` 前必须由基础设施负责人确认：

- 有专用测试 Docker 主机，GitHub runner 能通过 SSH 访问；若测试主机只在公司内网，应使用具备内网连通性的 self-hosted runner，或提供受控网络入口；
- 测试主机已安装 Docker，并允许 SSH 用户执行 Docker 命令；
- 测试主机使用隔离数据库/配置，不连接生产数据；
- 如需域名验收，DNS、反向代理和 HTTPS 已配置；默认 smoke URL 是测试主机本机端口，不依赖域名；
- GitHub Environment `test` 的审批策略和 secrets 已配置。

当前只提交 workflow，不自动触发测试环境部署。

## Secrets

建议将以下变量配置在 `test` Environment，禁止写入代码：

- `SWR_USERNAME` / `SWR_PASSWORD`
- `TEST_SSH_HOST` / `TEST_SSH_PORT` / `TEST_SSH_USER`
- `TEST_SSH_PRIVATE_KEY` / `TEST_SSH_KNOWN_HOSTS`

PR CI 不需要这些 secrets，来自 fork 的 PR 也不应获得它们。

## 推荐执行顺序

1. PR 打开或更新，确认 `ci.yml` 的三个 job 通过；
2. 手动运行 `Build Test Image`，填写源 ref 和不可变 `image_tag`；
3. 确认 SWR 中镜像存在后，手动运行 `Deploy Test Environment`；
4. 填写同一个 `image_tag`、Docker 容器名、主机端口和 smoke URL；
5. 核对容器日志以及 `/healthz`、`/api/health`、`/api/routes`；
6. 通过后再将 workflow 结构抽成多项目 reusable workflow。

生产 `deploy.yml` 暂不改动，避免测试方案未经验证就改变生产发布链路。
