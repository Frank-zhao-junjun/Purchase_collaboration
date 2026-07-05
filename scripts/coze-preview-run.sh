#!/usr/bin/env bash
set -euo pipefail

# 基于脚本位置定位项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 显式声明关键环境变量
export PORT=5000

# 清理 5000 端口残留进程（绝不碰 9000）
fuser -k 5000/tcp 2>/dev/null || true
sleep 1

# 启动后端服务（后台运行，端口 8000）
cd backend
python3 init_db.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 > /app/work/logs/bypass/app.log 2>&1 &
cd ..

# 等待后端就绪
for i in $(seq 1 15); do
  if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
    echo "[coze-preview-run] Backend ready on port 8000"
    break
  fi
  sleep 1
done

# 启动前端 Vite 开发服务器（前台常驻，端口 5000）
cd frontend
exec pnpm exec vite --host 0.0.0.0 --port 5000
