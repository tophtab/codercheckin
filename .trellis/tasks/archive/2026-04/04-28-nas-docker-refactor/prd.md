# brainstorm: NAS Docker refactor

## Goal

将项目从 `CircleCI + Cloudflare Worker` 驱动的远程自动签到仓库，重构为面向本地环境和 NAS 的部署方案。新的主路径应围绕 Python 直接运行与 Docker / Docker Compose 部署展开，清理不再维护的 CI/CD、Cloudflare Worker 和英文文档。

## What I already know

* 用户希望把项目改成本地版、NAS 版、Docker 版部署，不再考虑现有 CI/CD 和 Cloudflare Worker 方案
* 用户希望删除英文 README，只保留中文文档
* 当前仓库已经有本地执行入口 `run.py`
* 当前仓库已经有 `Dockerfile`、`docker-compose.yml`、`docker-compose.build.yml`
* 当前 `README.md` 已经新增了 NAS / Docker Compose / 本地调试内容，但主体仍然以 CircleCI 和 Cloudflare Worker 为主
* 仓库仍然包含 `.circleci/config.yml`、`.github/workflows/*`、`worker.js`、`wrangler.toml`、`cloudflareworkers/`
* 当前工作区有未提交变更，涉及 README、GitHub workflow、Cookie Cloud、通知和若干平台逻辑，后续修改必须避免覆盖这些已有工作

## Assumptions (temporary)

* Python 运行和 Docker Compose 部署都会保留
* 旧的 CircleCI / Cloudflare Worker 相关目录和文档将被彻底下线，而不是仅标记废弃
* 仍然需要保留 Cookie Cloud、Telegram 通知，以及现有各平台签到逻辑

## Open Questions

* 调度时间配置是否采用 Cron 表达式作为统一接口，例如 `TZ=Asia/Shanghai` + `CHECKIN_CRON=0 9 * * *`？

## Requirements (evolving)

* README 重写为中文主文档，聚焦本地运行、NAS、Docker
* 删除英文 README
* 清理 CircleCI、Cloudflare Worker 相关实现和文档
* 保留 Docker 镜像发布能力，但将其定位为镜像分发，而非自动签到执行链路
* 保留并梳理 Python 直接运行方案
* 保留并梳理 Docker / Docker Compose 部署方案
* Docker / NAS 方案中的容器需要内置定时调度并常驻运行
* 重构后的仓库结构应与新的部署方式一致，避免保留误导性历史文件

## Acceptance Criteria (evolving)

* [ ] 仓库不再依赖 CircleCI / Cloudflare Worker 相关文件与说明
* [ ] 中文 README 能完整说明本地运行与 NAS / Docker 部署
* [ ] 英文 README 被移除
* [ ] Python 和 Docker 两条使用路径都能从仓库结构和文档中清晰体现
* [ ] Docker 镜像发布工作流仍可作为镜像分发方式保留
* [ ] `docker compose up -d` 后容器可常驻并按天自动执行签到

## Definition of Done (team quality bar)

* Tests added/updated (unit/integration where appropriate)
* Lint / typecheck / CI green
* Docs/notes updated if behavior changes
* Rollout/rollback considered if risky

## Out of Scope (explicit)

* 新增更多签到平台
* 重写现有各平台签到业务逻辑
* 设计新的云端自动调度方案

## Technical Notes

* 已检查文件：`README.md`、`README-en.md`、`Dockerfile`、`docker-compose.yml`、`run.py`、`worker.js`、`wrangler.toml`
* 已识别待清理的历史方案文件：
  - `.circleci/config.yml`
  - `.github/workflows/deploy-circleci.yml`
  - `.github/workflows/setup-workers.yml`
  - `worker.js`
  - `wrangler.toml`
  - `cloudflareworkers/`
* 已识别需保留并重新定位的文件：
  - `.github/workflows/dockerhub-publish.yml`：保留，用于 Docker 镜像发布
* 已识别当前已有但未提交的本地化方向改动：
  - README 中新增 Docker / NAS / Cookie Cloud 内容
  - Dockerfile 与 compose 文件已可支撑本地执行
* 新增约束：
  - 原 `docker-compose.yml` 当前为一次性执行模型，需要调整为常驻调度模型
