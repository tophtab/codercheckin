# CloudCheckin

面向本地环境和 NAS 的多平台自动签到项目，主路径是：

- Python 直接运行
- Docker 镜像部署
- Docker Compose 常驻调度

容器默认使用 `Asia/Shanghai` 时区，并在凌晨 `03:00` 执行每日签到。这个默认值落在 `00:00-08:00` 区间内，适合 NAS 长期后台运行。

## 支持平台

- `Nodeseek`：自动签到
- `Deepflood`：自动签到
- `V2EX`：自动签到

## 运行方式

### 推荐：NAS / Docker Compose 常驻运行

1. 准备环境变量文件：

```bash
cp .env.localtest.example .env
```

2. 编辑 `.env`，至少补充你要启用的平台 Cookie。

如果你本身在用 Cookie Cloud，更推荐直接配置 Cookie Cloud，而不是长期手动维护各站点 Cookie。

3. 启动常驻容器：

```bash
docker compose up -d
```

4. 查看日志：

```bash
docker compose logs -f cloudcheckin
```

默认容器会一直运行，并按照下面的配置定时执行：

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

### 使用已发布镜像

默认 `docker-compose.yml` 会直接拉取镜像：

```yaml
services:
  cloudcheckin:
    image: ${CLOUDCHECKIN_IMAGE:-tophtab/cloudcheckin:latest}
```

常见操作：

```bash
docker compose pull
docker compose up -d
docker compose logs -f cloudcheckin
```

### 从当前源码构建镜像

如果你不想直接拉取 Docker Hub 镜像，可以在本地或 NAS 上从源码构建：

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
```

### 手动立即执行一次

常驻容器用于定时跑任务；如果你想立刻手动跑一次：

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
CHECKIN_TARGETS=nodeseek,deepflood,v2ex
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
pip install -r requirements.txt
cp .env.localtest.example .env
python run.py
```

如果只想单独调试某个平台，也可以直接执行：

```bash
python -m nodeseek.nodeseek
python -m deepflood.deepflood
python -m v2ex.v2ex
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
