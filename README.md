# CloudCheckin

多平台自动签到工具，适合 Docker / NAS 部署。支持 Cookie Cloud 同步 Cookie、Telegram 通知和定时执行。

## Docker Compose

新建 `compose.yaml`：

```yaml
services:
  cloudcheckin:
    image: ${CLOUDCHECKIN_IMAGE:-tophtab/cloudcheckin:latest}
    restart: unless-stopped
    env_file:
      - .env
    environment:
      CHECKIN_TARGETS: "${CHECKIN_TARGETS:-nodeseek,deepflood,v2ex}"
      CHECKIN_CRON: "${CHECKIN_CRON:-30 3 * * *}"
      PYTHONUNBUFFERED: "1"
      TZ: "${TZ:-Asia/Shanghai}"
```

新建 `.env`，推荐使用 Cookie Cloud：

```env
COOKIE_CLOUD_URL=http://your-cookiecloud-host:8088
COOKIE_CLOUD_UUID=your-uuid
COOKIE_CLOUD_PASSWORD=your-password
```

也可以手动配置 Cookie：

```env
NODESEEK_COOKIE=your_cookie_here
DEEPFLOOD_COOKIE=your_cookie_here
V2EX_COOKIE='your_v2ex_cookie_here'
```

可选配置：

```env
CHECKIN_TARGETS=nodeseek,deepflood,v2ex
CHECKIN_CRON=30 3 * * *
TZ=Asia/Shanghai
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

启动并查看日志：

```bash
docker compose up -d
docker compose logs -f cloudcheckin
```

更新镜像：

```bash
docker compose pull
docker compose up -d
```

立即执行一次：

```bash
docker compose run --rm cloudcheckin python run.py
```

## 支持平台

| 平台 | 多账号 | Cookie Cloud |
|------|--------|--------------|
| Nodeseek | 是 | 是 |
| Deepflood | 是 | 是 |
| V2EX | 否 | 是 |

## 使用仓库模板

```bash
git clone https://github.com/tophtab/CloudCheckin.git
cd CloudCheckin
cp .env.localtest.example .env
docker compose up -d
```

## 本地开发

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.localtest.example .env
python run.py
pytest
```

单独测试平台：

```bash
python -m nodeseek.nodeseek
python -m deepflood.deepflood
python -m v2ex.v2ex
```

## 说明

- `NODESEEK_COOKIE` / `DEEPFLOOD_COOKIE` 支持多账号，用 `&` 分隔。
- 每个启用平台都需要 Cookie，可来自环境变量或 Cookie Cloud。
- 容器启动时会校验 Cookie 来源，失败会退出并在日志中提示缺少的平台。
- 建议将签到时间设置在凌晨 0:00-8:00 之间。

## License

MIT
