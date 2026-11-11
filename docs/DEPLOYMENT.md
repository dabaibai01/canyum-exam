# 可以云码考试系统 · 部署手册

本文按「一台 Linux 云服务器 + Nginx + Supervisor + SQLite」的典型单机部署方式编写。文中的域名、IP、目录、密码均为占位示例，请替换成自己的信息。

## 1. 部署架构

```text
浏览器
  ├── https://exam.example.com   → Nginx → /var/www/canyum-exam/student
  └── https://admin.example.com  → Nginx → /var/www/canyum-exam/admin
                                      └── /api/ 反代 → 127.0.0.1:8000
                                                          │
                                                    FastAPI + Uvicorn
                                                          │
                                              backend/data/test.db（SQLite）
```

- 学员端、管理端是两个独立的 Vue 静态站点。
- 后端只监听 `127.0.0.1:8000`，由 Nginx 统一对外提供 HTTPS。
- 默认数据库是 SQLite，单机、中小规模使用足够；需要 MySQL 时可参考 `database/init.sql`，但本项目的模型默认连接 SQLite。

## 2. 服务器准备

推荐配置（50 人以内日常使用）：

| 项目 | 最低 | 推荐 |
| --- | --- | --- |
| CPU | 2 核 | 4 核 |
| 内存 | 2 GB | 4 GB |
| 系统盘 | 40 GB | 50 GB |
| 带宽 | 3 Mbps | 5 Mbps |
| 系统 | Ubuntu 20.04+ / Debian 11+ / CentOS 7.9+ | Ubuntu 22.04 LTS |

需要开放的端口：

| 端口 | 用途 |
| --- | --- |
| 22 | SSH |
| 80 | HTTP（申请证书、跳转 HTTPS） |
| 443 | HTTPS |

安装基础软件（Ubuntu / Debian）：

```bash
sudo apt update
sudo apt install -y nginx supervisor python3 python3-venv python3-pip git curl
```

CentOS 7 请使用 `yum`；如果系统 Python 版本低于 3.10，建议安装 Python 3.11 或使用自带 OpenSSL 的便携版 Python，避免 `pip` 因 SSL 版本过低失败。

## 3. 上传代码

在服务器创建目录：

```bash
sudo mkdir -p /var/www/canyum-exam
sudo chown -R $USER:$USER /var/www/canyum-exam
```

从本地把**源码**上传到服务器（不要上传 `node_modules`、`dist`、`test.db`、`uploads`）：

```bash
rsync -avz --exclude node_modules --exclude dist --exclude '*.db' \
  ./canyum-exam/ root@SERVER_IP:/var/www/canyum-exam/
```

如果使用 Git 仓库，也可以直接在服务器 `git clone`。

## 4. 部署后端

```bash
cd /var/www/canyum-exam/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

创建数据目录和环境变量：

```bash
mkdir -p data
cp ../.env.example .env
```

编辑 `backend/.env`：

```dotenv
SECRET_KEY=换成一串足够长的随机字符
DATABASE_PATH=/var/www/canyum-exam/backend/data/test.db
CORS_ORIGINS=https://exam.example.com,https://admin.example.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=首次登录后请立即修改
TOKEN_EXPIRE_MINUTES=720
```

> `SECRET_KEY` 可以用 `openssl rand -hex 32` 生成。不要把真实 `.env` 提交到 Git。

首次启动（前台运行，确认能起来）：

```bash
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000
```

另开一个终端验证：

```bash
curl http://127.0.0.1:8000/api/health
```

看到 `{"status":"ok","message":"服务正常运行"}` 表示后端正常。首次启动会自动建表并创建管理员账号。

按 `Ctrl+C` 停止前台进程，交给 Supervisor 守护。

## 5. 构建两个前端

在服务器上构建（或者本地构建后只上传 `dist`）：

```bash
cd /var/www/canyum-exam/frontend
npm ci
npm run build

cd /var/www/canyum-exam/admin
npm ci
npm run build
```

构建产物：

```text
frontend/dist/  → 复制为 /var/www/canyum-exam/student
admin/dist/     → 复制为 /var/www/canyum-exam/admin
```

示例：

```bash
rm -rf /var/www/canyum-exam/student /var/www/canyum-exam/admin
cp -r /var/www/canyum-exam/frontend/dist /var/www/canyum-exam/student
cp -r /var/www/canyum-exam/admin/dist /var/www/canyum-exam/admin
```

> 前端构建时 `/api` 由 Nginx 反代，不需要修改前端里的后端地址。

## 6. 配置 Supervisor

复制模板并修改路径、用户和环境变量：

```bash
sudo cp /var/www/canyum-exam/deploy/supervisor/canyum-backend.conf /etc/supervisor/conf.d/
sudo nano /etc/supervisor/conf.d/canyum-backend.conf
```

确认以下三项与实际环境一致：

- `directory`：后端目录
- `command`：`.venv/bin/uvicorn` 的路径
- `environment`：`SECRET_KEY`、`DATABASE_PATH`、`CORS_ORIGINS`

如果使用 `deploy/backend/env.sh`，也可以把 `command` 改为：

```ini
command=/bin/bash -lc "source /var/www/canyum-exam/deploy/backend/env.sh && exec /var/www/canyum-exam/backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000"
```

加载并启动：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status canyum-backend
```

看到 `RUNNING` 即成功。查看日志：

```bash
sudo tail -f /var/log/canyum-backend.log
```

> 宝塔面板用户注意：`supervisorctl` 可能在宝塔的 Python 环境中，实际路径常为 `/www/server/panel/pyenv/bin/supervisorctl`；进程名必须使用完整组名，例如 `canyum-backend`。

## 7. 配置 Nginx

复制两个模板：

```bash
sudo cp /var/www/canyum-exam/deploy/nginx/student.conf.example /etc/nginx/conf.d/canyum-student.conf
sudo cp /var/www/canyum-exam/deploy/nginx/admin.conf.example /etc/nginx/conf.d/canyum-admin.conf
```

把 `exam.example.com`、`admin.example.com` 改成实际域名；把 `root` 指向上一步的 `student` / `admin` 目录。

检查并重载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

先用 HTTP 访问两个域名，确认页面能打开、接口能通。再申请 HTTPS：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d exam.example.com -d admin.example.com
```

证书生效后，把 HTTP 全部跳转到 HTTPS。可按需只允许管理端从固定 IP 访问，例如在 `admin.conf` 里加：

```nginx
allow 203.0.113.10;
deny all;
```

## 8. 首次使用

1. 打开管理端：`https://admin.example.com`
2. 使用 `.env` 中的管理员账号登录（默认 `admin / admin123`）
3. 立即进入「系统设置 → 账号安全」修改密码
4. 进入「系统设置 → 品牌设置」修改系统名称、副标题、Logo、开发者、页脚和备案号
5. 进入「分类管理」创建分类
6. 进入「题库管理 → 批量导入」导入题库
7. 创建考试、发布公告
8. 打开学员端：`https://exam.example.com`，用学员账号登录验证

## 9. 备份与升级

### 备份

需要备份的内容：

```text
backend/data/test.db        # 数据库
backend/uploads/            # 题目图片、Logo
backend/.env                # 环境变量
```

示例备份脚本：

```bash
#!/usr/bin/env bash
set -e
STAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/var/backups/canyum-exam
mkdir -p "$BACKUP_DIR"
cp /var/www/canyum-exam/backend/data/test.db "$BACKUP_DIR/test.db.$STAMP"
tar -czf "$BACKUP_DIR/uploads.$STAMP.tar.gz" -C /var/www/canyum-exam/backend uploads
find "$BACKUP_DIR" -type f -mtime +14 -delete
```

建议每天执行一次，并把备份同步到另一台机器或对象存储。

### 升级

1. 先备份数据库和 `uploads`。
2. 上传新代码，保留 `backend/.env`、`backend/data`、`backend/uploads`。
3. 如果依赖有变化：`pip install -r requirements.txt`。
4. 重新构建 `frontend` / `admin` 并替换 `student` / `admin`。
5. 执行 `sudo supervisorctl restart canyum-backend`。
6. 检查 `/api/health`、登录、题库和设置页。

> 不要用含数据库的整站压缩包覆盖线上数据库，除非确认要恢复旧数据。

## 10. 常见问题

| 现象 | 排查 |
| --- | --- |
| 页面打不开 | `nginx -t`、`systemctl status nginx`、域名解析、安全组 80/443 |
| 页面能开但接口 502 | `supervisorctl status`、`curl 127.0.0.1:8000/api/health`、后端日志 |
| 登录后立刻退出 | `CORS_ORIGINS` 是否包含实际域名、浏览器是否禁用 Cookie、`SECRET_KEY` 是否变化 |
| 上传 Logo 失败 | Nginx `client_max_body_size` 是否 ≥ 25m；Logo 是否 ≤ 2MB |
| 导入题库失败 | 分类是否存在、表头是否为「分类/题型/题干/正确答案」、答案字母是否在选项范围内 |
| 修改名称不生效 | 后端是否重启、浏览器是否缓存；强制刷新 `Ctrl+F5` |
| 数据库锁/写入失败 | 确认只有一个后端进程使用同一个 SQLite 文件，检查磁盘空间和权限 |
| CentOS 7 pip SSL 报错 | 使用自带 OpenSSL 的 Python 3.11，或改用离线 wheel 安装 |

## 11. 安全检查清单

- [ ] 修改默认管理员密码
- [ ] 修改 `SECRET_KEY`
- [ ] 生产环境关闭或限制 `/docs` 公网访问
- [ ] 管理端使用独立域名，必要时限制来源 IP
- [ ] 开启 HTTPS，禁止明文登录
- [ ] 定期备份数据库和上传目录
- [ ] 不把 `.env`、`test.db`、`uploads` 提交到 Git
- [ ] 服务器只开放 22 / 80 / 443，后端 8000 不对外
