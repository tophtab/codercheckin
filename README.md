# CloudCheckin

面向本地环境和 NAS 的多平台自动签到项目。当前推荐部署方式是
Docker Compose 常驻运行：容器启动后不会立刻退出，而是按 Cron 表达式定时执行签到。

项目支持三种运行方式：

- Python 直接运行
- Docker 镜像部署
- Docker Compose 常驻调度

容器默认使用 `Asia/Shanghai` 时区，并在凌晨 `03:00` 执行每日签到。这个默认值落在 `00:00-08:00` 区间内，适合 NAS 长期后台运行。

## 支持平台

- `Nodeseek`：自动签到
- `Deepflood`：自动签到
- `V2EX`：自动签到

## 推荐部署：NAS / Docker Compose

这个仓库的 [docker-compose.yml](/home/toph/CloudCheckin/docker-compose.yml:1) 用来直接拉取已发布镜像并启动常驻调度容器。默认配置如下：

```yaml
services:
  cloudcheckin:
    image: ${CLOUDCHECKIN_IMAGE:-tophtab/cloudcheckin:latest}
    restart: unless-stopped
    env_file:
      - .env
    environment:
      CHECKIN_TARGETS: "${CHECKIN_TARGETS:-nodeseek,deepflood,v2ex}"
      CHECKIN_CRON: "${CHECKIN_CRON:-0 3 * * *}"
      PYTHONUNBUFFERED: "1"
      TZ: "${TZ:-Asia/Shanghai}"
```

含义：

- `image`：默认使用 `tophtab/cloudcheckin:latest`，也可以通过 `.env` 里的 `CLOUDCHECKIN_IMAGE` 覆盖
- `restart: unless-stopped`：NAS 重启或 Docker 服务重启后自动恢复运行
- `env_file: .env`：从 `.env` 读取 Cookie、Telegram、Cookie Cloud 等配置
- `CHECKIN_TARGETS`：控制要执行的平台，默认全部执行
- `CHECKIN_CRON`：控制定时执行时间，默认每天 `03:00`
- `TZ`：控制容器内时区，默认 `Asia/Shanghai`

如果 NAS 面板要求文件名必须是 `compose.yaml`，可以把本仓库的 `docker-compose.yml` 内容复制到面板生成的 `compose.yaml`；命令行使用时保留 `docker-compose.yml` 即可。

### 启动步骤

1. 准备 `.env`：

```bash
cp .env.localtest.example .env
```

2. 编辑 `.env`，至少补充你要启用的平台 Cookie，或配置 Cookie Cloud。

如果你本身在用 Cookie Cloud，更推荐直接配置 Cookie Cloud，而不是长期手动维护各站点 Cookie。

3. 启动：

```bash
docker compose up -d
```

4. 查看日志：

```bash
docker compose logs -f cloudcheckin
```

启动后容器会一直运行，日志里会打印下一次执行时间。默认调度配置等价于：

```env
TZ=Asia/Shanghai
CHECKIN_CRON=0 3 * * *
CHECKIN_TARGETS=nodeseek,deepflood,v2ex
```

如果你想修改执行时间，直接调整 `CHECKIN_CRON` 即可。建议仍然放在凌晨 `00:00-08:00` 区间，例如：

```env
CHECKIN_CRON=30 2 * * *
CHECKIN_CRON=0 5 * * *
CHECKIN_CRON=15 7 * * *
```

### 更新已发布镜像

如果你使用默认的 Docker Hub 镜像，更新时执行：

```bash
docker compose pull
docker compose up -d
docker compose logs -f cloudcheckin
```

### 从当前源码构建镜像

如果你不想拉取 Docker Hub 镜像，可以叠加 [docker-compose.build.yml](/home/toph/CloudCheckin/docker-compose.build.yml:1) 从当前源码构建：

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
```

### 手动立即执行一次

常驻容器默认只负责定时执行。如果你想立刻跑一次，不需要等待下一次 Cron：

```bash
docker compose run --rm cloudcheckin python run.py
```

## 环境变量

### 平台 Cookie

```env
V2EX_COOKIE=
NODESEEK_COOKIE=
DEEPFLOOD_COOKIE=
```

说明：

- `NODESEEK_COOKIE` 和 `DEEPFLOOD_COOKIE` 支持多账号，使用 `&` 分隔
- 如果手动填写 `V2EX_COOKIE`，建议写成 `V2EX_COOKIE='原始 cookie'`，避免 `.env` 里的 `$` 被 `docker compose` 当成变量插值
- 如果对应平台的直接 Cookie 留空，程序会继续尝试从 Cookie Cloud 自动匹配

### Telegram 通知

```env
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
```

如果未配置 Telegram，签到逻辑仍会执行，但不会发送通知。

### 调度与镜像

```env
CLOUDCHECKIN_IMAGE=tophtab/cloudcheckin:latest
CHECKIN_TARGETS=nodeseek,deepflood,v2ex
TZ=Asia/Shanghai
CHECKIN_CRON=0 3 * * *
```

说明：

- `CHECKIN_TARGETS` 用逗号分隔，可只跑部分平台
- `TZ` 控制容器内调度时区
- `CHECKIN_CRON` 使用标准 5 段 Cron 表达式

例如只执行部分平台：

```env
CHECKIN_TARGETS=nodeseek,v2ex
```

## Cookie Cloud

这是当前更推荐的方案。你只维护 Cookie Cloud，仓库侧尽量少放平台专属 Cookie。

如果不想手动维护各平台 Cookie，可以启用 [Cookie Cloud](https://github.com/easychen/CookieCloud)：

```env
COOKIE_CLOUD_URL=http://your-cookiecloud-host:8088
COOKIE_CLOUD_UUID=your-uuid
COOKIE_CLOUD_PASSWORD=your-password
COOKIE_CLOUD_CRYPTO_TYPE=
```

读取优先级如下：

1. 先读取平台专属环境变量
2. 对应环境变量为空时，再尝试从 Cookie Cloud 自动匹配

如果你偏好完全交给 Cookie Cloud，可以把下面这些平台变量都留空：

```env
V2EX_COOKIE=
NODESEEK_COOKIE=
DEEPFLOOD_COOKIE=
```

当前支持自动匹配以下站点：

- `nodeseek.com`
- `deepflood.com`
- `v2ex.com`

## 本地 Python 运行

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
cp .env.localtest.example .env
python run.py
```

如果只想单独调试某个平台，也可以直接执行：

```bash
python -m nodeseek.nodeseek
python -m deepflood.deepflood
python -m v2ex.v2ex
```

## 测试

仓库现在已经补上了 Python 项目配置和最小测试入口：

- [pyproject.toml](/home/toph/CloudCheckin/pyproject.toml:1)
- [pytest.ini](/home/toph/CloudCheckin/pytest.ini:1)
- [tests/test_checkin_response.py](/home/toph/CloudCheckin/tests/test_checkin_response.py:1)
- [tests/test_checkin_runner.py](/home/toph/CloudCheckin/tests/test_checkin_runner.py:1)

本地运行测试：

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
pytest
```

## 发布 Docker 镜像

仓库保留了 GitHub Actions 的 Docker 镜像发布工作流：`.github/workflows/dockerhub-publish.yml`。

需要的配置：

- `DOCKERHUB_USERNAME`：Docker Hub 用户名
- `DOCKERHUB_TOKEN`：Docker Hub Access Token
- 可选 `DOCKERHUB_IMAGE`：自定义镜像名，未配置时默认发布到 `<DOCKERHUB_USERNAME>/cloudcheckin`

触发方式：

- push 到 `main`
- push `v*` tag
- 手动执行 `workflow_dispatch`

## 目录说明

- [run.py](/home/toph/CloudCheckin/run.py:1)：单次执行入口
- [scheduler.py](/home/toph/CloudCheckin/scheduler.py:1)：容器常驻调度入口
- [checkin_runner.py](/home/toph/CloudCheckin/checkin_runner.py:1)：平台批量执行器
- [docker-compose.yml](/home/toph/CloudCheckin/docker-compose.yml:1)：常驻调度部署
- [docker-compose.build.yml](/home/toph/CloudCheckin/docker-compose.build.yml:1)：本地构建镜像覆盖配置

## 说明

- 这个项目已经不再维护 CircleCI、Cloudflare Worker 等旧部署方案
- 当前推荐部署模型就是本地 / NAS + Docker Compose 常驻运行
- 如果某个平台 Cookie 失效，更新 `.env` 后重启容器即可
