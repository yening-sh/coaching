#!/usr/bin/env bash
# dev.sh — 一键启动开发环境
# 用法：bash dev.sh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

# ── 颜色 ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()  { echo -e "${GREEN}▶ $*${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $*${NC}"; }
error() { echo -e "${RED}✗ $*${NC}"; exit 1; }

# ── 检查 PostgreSQL ──────────────────────────────────────────────────────────
info "检查 PostgreSQL..."
if ! command -v psql &>/dev/null; then
    warn "未找到 psql，尝试通过 Homebrew 安装 PostgreSQL..."
    if ! command -v brew &>/dev/null; then
        error "未安装 Homebrew，请先安装：https://brew.sh"
    fi
    brew install postgresql@17
    echo 'export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"' >> ~/.zprofile
    export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
fi

# 启动 PostgreSQL（如果没在运行）
if ! pg_isready -q 2>/dev/null; then
    info "启动 PostgreSQL..."
    brew services start postgresql@17 2>/dev/null || brew services start postgresql 2>/dev/null || true
    sleep 2
fi

if ! pg_isready -q 2>/dev/null; then
    error "PostgreSQL 启动失败，请手动运行: brew services start postgresql@17"
fi
echo "  ✓ PostgreSQL 运行中"

# ── 创建数据库（如不存在）────────────────────────────────────────────────────
DB_NAME="coaching"
if ! psql -lqt 2>/dev/null | cut -d\| -f1 | grep -qw "$DB_NAME"; then
    info "创建数据库 $DB_NAME..."
    createdb "$DB_NAME" 2>/dev/null || warn "无法自动创建数据库，请手动运行: createdb $DB_NAME"
fi

# ── 后端虚拟环境 ─────────────────────────────────────────────────────────────
info "检查后端虚拟环境..."
if [ ! -d "$BACKEND/venv" ]; then
    info "创建虚拟环境..."
    python3 -m venv "$BACKEND/venv"
fi
source "$BACKEND/venv/bin/activate"

info "安装/更新 Python 依赖..."
pip install -q -r "$BACKEND/requirements.txt"

# ── 初始化数据库 ─────────────────────────────────────────────────────────────
info "初始化数据库（幂等，安全重复运行）..."
cd "$BACKEND"
python init_db.py

# ── 启动后端 ─────────────────────────────────────────────────────────────────
info "启动后端 (http://localhost:8000)..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# ── 启动前端 ─────────────────────────────────────────────────────────────────
cd "$FRONTEND"
if [ ! -d "node_modules" ]; then
    info "安装前端依赖..."
    npm install
fi

info "启动前端 (http://localhost:5173)..."
npm run dev &
FRONTEND_PID=$!

# ── 等待并清理 ───────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}✅ 开发环境已启动${NC}"
echo ""
echo "  前端：http://localhost:5173"
echo "  后端：http://localhost:8000/docs"
echo ""
echo "  管理员账号: admin / admin123"
echo ""
echo "  按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
