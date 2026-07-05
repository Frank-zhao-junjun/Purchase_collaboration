#!/usr/bin/env bash
set -euo pipefail

# 基于脚本位置定位项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "[coze-deploy-build] Installing frontend dependencies..."
cd frontend && pnpm install && cd ..

echo "[coze-deploy-build] Installing backend dependencies..."
pip3 install -r backend/requirements.txt

echo "[coze-deploy-build] Building frontend..."
cd frontend && pnpm run build && cd ..

echo "[coze-deploy-build] Done."
