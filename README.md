# CloudCheckin - 多平台自动签到工具

一个专为 NAS 和本地环境设计的自动签到工具，支持 Docker 部署，开箱即用。

## 为什么选择 CloudCheckin？

- 🚀 **开箱即用**：Docker Compose 一键部署，无需复杂配置
- 🔄 **自动运行**：容器常驻后台，按时自动签到，无需手动干预
- 🍪 **Cookie Cloud 集成**：支持从 Cookie Cloud 自动同步 Cookie，告别手动维护
- 📱 **Telegram 通知**：签到结果实时推送，随时掌握状态
- 🔐 **多账号支持**：单个平台可配置多个账号同时签到
- 🌏 **时区友好**：默认使用 `Asia/Shanghai` 时区，可自定义

## 支持平台

| 平台 | 多账号 | Cookie Cloud |
|------|--------|--------------|
| Nodeseek | ✅ | ✅ |
| Deepflood | ✅ | ✅ |
| V2EX | ❌ | ✅ |

## 快速开始

### 1. 准备配置文件

```bash
# 克隆或下载本仓库
git clone https://github.com/tophtab/CloudCheckin.git
cd CloudCheckin

# 复制配置模板
cp .env.localtest.example .env
```

### 2. 编辑 `.env` 文件

**方式一：使用 Cookie Cloud（推荐）**

如果你已经在使用 [Cookie Cloud](https://github.com/easychen/CookieCloud)，只需配置：

```env
COOKIE_CLOUD_URL=http://your-cookiecloud-host:8088
COOKIE_CLOUD_UUID=your-uuid
COOKIE_CLOUD_PASSWORD=your-password
```

程序会自动从 Cookie Cloud 获取所需平台的 Cookie，无需手动维护。

**方式二：手动配置 Cookie**

如果不使用 Cookie Cloud，可以手动填写各平台 Cookie：

```env
# 单账号
NODESEEK_COOKIE=your_cookie_here

# 多账号（使用 & 分隔）
NODESEEK_COOKIE=account1_cookie&account2_cookie&account3_cookie

# V2EX（注意：如果 Cookie 包含 $ 符号，需要用单引号包裹）
V2EX_COOKIE='your_v2ex_cookie_here'
```

**可选：配置 Telegram 通知**

```env
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. 启动容器

```bash
docker compose up -d
```

### 4. 查看日志

```bash
docker compose logs -f cloudcheckin
```

你会看到类似输出：

```
Scheduler started with TZ=Asia/Shanghai, CHECKIN_CRON=0 3 * * *, CHECKIN_TARGETS=nodeseek,deepflood,v2ex
Next run scheduled at 2026-04-29T03:00:00+08:00
```

容器会在每天凌晨 3 点自动执行签到。

## 进阶配置

### 自定义执行时间

编辑 `.env` 文件，修改 `CHECKIN_CRON`：

```env
# 每天凌晨 2:30 执行
CHECKIN_CRON=30 2 * * *

# 每天早上 8:00 执行
CHECKIN_CRON=0 8 * * *

# 每天凌晨 5:15 执行
CHECKIN_CRON=15 5 * * *
```

修改后重启容器：

```bash
docker compose restart
```

### 只签到部分平台

```env
# 只签到 Nodeseek 和 V2EX
CHECKIN_TARGETS=nodeseek,v2ex

# 只签到 Deepflood
CHECKIN_TARGETS=deepflood
```

### 自定义时区

```env
# 使用美国东部时间
TZ=America/New_York

# 使用日本时间
TZ=Asia/Tokyo
```

### 手动立即执行一次

不想等到定时任务？可以立即执行一次：

```bash
docker compose run --rm cloudcheckin python run.py
```

## 更新镜像

当有新版本发布时：

```bash
docker compose pull
docker compose up -d
```

## 本地开发

如果你想修改代码或本地调试：

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -e .[dev]

# 配置环境变量
cp .env.localtest.example .env
# 编辑 .env 填入你的配置

# 运行签到
python run.py

# 运行测试
pytest
```

### 单独测试某个平台

```bash
python -m nodeseek.nodeseek
python -m deepflood.deepflood
python -m v2ex.v2ex
```

## 常见问题

### Q: 如何获取平台的 Cookie？

1. 在浏览器登录对应平台
2. 按 F12 打开开发者工具
3. 切换到 Network（网络）标签
4. 刷新页面，找到任意请求
5. 在请求头中找到 `Cookie` 字段，复制完整内容

### Q: Cookie 失效了怎么办？

**使用 Cookie Cloud：** Cookie Cloud 会自动同步最新 Cookie，无需手动更新

**手动配置：** 更新 `.env` 文件中的 Cookie，然后重启容器：

```bash
docker compose restart
```

### Q: 为什么没有收到 Telegram 通知？

1. 检查 `TELEGRAM_TOKEN` 和 `TELEGRAM_CHAT_ID` 是否正确
2. 确认 Bot 已经添加到对应的聊天中
3. 查看容器日志是否有错误信息

### Q: 如何在群晖 NAS 上部署？

1. 打开 Container Manager（原 Docker 套件）
2. 在项目中新建项目
3. 将本仓库的 `docker-compose.yml` 内容复制到 `compose.yaml`
4. 上传 `.env` 文件或在界面中配置环境变量
5. 启动项目

### Q: 支持添加新平台吗？

当然！项目采用模块化设计，添加新平台很简单。参考 `nodeseek/nodeseek.py` 或 `deepflood/deepflood.py` 的实现即可。

## 环境变量完整列表

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `CHECKIN_TARGETS` | 要执行的平台（逗号分隔） | `nodeseek,deepflood,v2ex` | 否 |
| `CHECKIN_CRON` | Cron 表达式 | `0 3 * * *` | 否 |
| `TZ` | 时区 | `Asia/Shanghai` | 否 |
| `NODESEEK_COOKIE` | Nodeseek Cookie（支持多账号，用 `&` 分隔） | - | 条件 |
| `DEEPFLOOD_COOKIE` | Deepflood Cookie（支持多账号，用 `&` 分隔） | - | 条件 |
| `V2EX_COOKIE` | V2EX Cookie | - | 条件 |
| `COOKIE_CLOUD_URL` | Cookie Cloud 服务地址 | - | 条件 |
| `COOKIE_CLOUD_UUID` | Cookie Cloud UUID | - | 条件 |
| `COOKIE_CLOUD_PASSWORD` | Cookie Cloud 密码 | - | 条件 |
| `COOKIE_CLOUD_CRYPTO_TYPE` | Cookie Cloud 加密类型 | - | 否 |
| `TELEGRAM_TOKEN` | Telegram Bot Token | - | 否 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | - | 否 |

**注意：** 
- 每个平台的 Cookie 可以通过直接配置或 Cookie Cloud 提供，至少需要一种方式
- Telegram 配置为可选，不配置也不影响签到功能

## 项目结构

```
CloudCheckin/
├── run.py                    # 单次执行入口
├── scheduler.py              # 定时调度入口（容器使用）
├── checkin_runner.py         # 平台批量执行器
├── attendance_checkin.py     # 通用签到流程
├── checkin_response.py       # 响应解析器
├── cookiecloud/              # Cookie Cloud 客户端
├── telegram/                 # Telegram 通知模块
├── nodeseek/                 # Nodeseek 平台实现
├── deepflood/                # Deepflood 平台实现
├── v2ex/                     # V2EX 平台实现
├── docker-compose.yml        # Docker Compose 配置
└── .env.localtest.example    # 环境变量模板
```

## 技术栈

- Python 3.11+
- Docker & Docker Compose
- curl_cffi（模拟浏览器请求）
- croniter（Cron 表达式解析）
- cryptography（Cookie Cloud 解密）

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**提示：** 建议将签到时间设置在凌晨 0:00-8:00 之间，避免与平台高峰期冲突。
