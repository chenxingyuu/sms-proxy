# SMS Proxy

## 项目简介

SMS Proxy 是一个基于 FastAPI 的短信代理服务，支持“移动 MAS 短信代理”和“飞书短信代理”两种短信通道，具备批量发送、重复短信过滤、异常告警等能力。适用于需要统一短信发送入口、批量处理和多通道告警的场景。

---

## 主要功能

- **移动 MAS 短信代理**：
  - 60 秒内重复短信自动过滤，防止重复发送。
  - 每 5 秒批量发送一次短信（受供应商 API 限制）。
  - 支持单条和多条短信发送。
- **飞书短信代理**：
  - 支持通过飞书机器人接口发送消息，实现短信/告警推送。
  - 支持内容过滤，60 秒内相同内容不重复推送。
  - 支持自定义过滤规则，灵活控制告警内容。
- **短信队列**：基于 Redis 实现短信队列，异步消费，提升吞吐量。
- **异常告警**：脚本异常时自动推送飞书消息。

---

## 目录结构

```
.
├── app/                # 业务代码（短信、飞书、WebSocket、公共模块）
├── cores/              # 配置、日志、Redis、短信核心逻辑
├── crontabs/           # 定时任务脚本（短信批量消费）
├── main.py             # 服务启动入口
├── requirements.txt    # 依赖包
├── config.ini          # 配置文件
├── docker-compose.yaml # Docker 编排
```

---

## 安装与部署

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd sms_proxy
```

### 2. 安装依赖

建议使用 Python 3.8+，并提前安装 Redis 服务。

```bash
pip install -r requirements.txt
```

### 3. 配置文件

复制并修改 `config.ini.example` 为 `config.ini`，根据实际情况填写：

- Redis 连接信息
- 飞书 webhook 配置
- MAS 短信平台参数
- 过滤规则参数

### 4. 启动服务

#### 本地启动

```bash
python main.py
```

#### Docker 启动

```bash
docker-compose up -d
```

---

## 配置说明

`config.ini` 示例：

```ini
[app]
project_name = SMS Proxy
api_version = /api/v1
debug = true
host = 0.0.0.0
port = 8000

[redis]
host = localhost
port = 6379
password = root
default_db = 0

[feishu]
webhook_url =
secret =

[mas]
app_id =
secret_key =
ec_name = 广州白云国际机场建设发展有限公司
api_url = https://112.35.10.201:28888/sms/norsubmit
sign =

[rules]
feishu_same_message_interval = 60
sms_same_message_interval = 60
```

---

## 主要接口说明

### 1. 移动 MAS 短信代理

- **接口**：`POST /mas/send`
- **鉴权**：需 API Key
- **请求体**：

```json
{
  "phone_numbers": ["138xxxxxx01", "138xxxxxx02"],
  "message": "测试短信内容"
}
```

- **返回**：

```json
{ "message": "SMS sent successfully" }
```

### 2. 飞书短信代理（消息/告警推送）

- **接口**：`POST /feishu/send/{token}`
- **请求体**：飞书消息格式
- **说明**：支持内容过滤，60 秒内相同内容不重复推送。

### 3. 飞书过滤规则配置

- **添加规则**：`POST /feishu/config/{token}`
- **删除规则**：`DELETE /feishu/config/{token}`

---

## 定时任务说明

- `crontabs/task.py`：每 5 秒消费 Redis 队列，批量发送短信，单次最多 100 条。
- 可通过 Docker Compose 启动 `task` 服务，自动运行定时任务。

---

## 常见问题

1. **Redis 连接失败**：请确保 Redis 服务已启动，配置文件参数正确。
2. **短信未发送**：检查 MAS 平台参数、API Key 配置及 Redis 队列状态。
3. **飞书告警无响应**：检查 webhook 配置及过滤规则设置。

---

## 贡献与反馈

如有建议或问题，欢迎提 Issue 或 PR。

---

如需补充接口文档、示例代码或其他说明，请告知！
