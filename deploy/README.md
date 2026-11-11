# 部署模板

这些文件是**示例**，复制到实际服务器后请按域名、目录和账号修改。

| 文件 | 用途 |
| --- | --- |
| `nginx/student.conf.example` | 学员端站点，`/api` 反代到后端 |
| `nginx/admin.conf.example` | 管理端站点，`/api` 反代到后端 |
| `supervisor/canyum-backend.conf` | Supervisor 守护后端 |
| `backend/env.sh.example` | 后端环境变量模板 |

生产部署完整步骤见 [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md)。
