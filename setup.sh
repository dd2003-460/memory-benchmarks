#!/bin/bash
# LoCoMo benchmark 环境初始化脚本
# 用法: ./setup.sh

set -e

VENV_DIR="/Users/a1-6/Desktop/workspace/tools/mb-server-venv"
REQ_FILE="$(dirname "$0")/requirements.txt"

echo "🚀 LoCoMo benchmark 环境初始化"
echo "========================================"

# 1. 创建虚拟环境（如果不存在）
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 创建虚拟环境: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
else
    echo "✅ 虚拟环境已存在: $VENV_DIR"
fi

# 2. 安装依赖
echo "📥 安装依赖..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$REQ_FILE" -q

# 3. 创建 .env 文件（如果不存在）
ENV_FILE="$(dirname "$0")/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 创建 .env 文件: $ENV_FILE"
    cat > "$ENV_FILE" << 'EOF'
# LoCoMo benchmark 配置
VLLM_API_KEY=sk-vllm-17L3d6z60EuhN1yW_bcRoynvDmxoAk1GKsF3QvSV9cY
VLLM_BASE_URL=http://100.112.53.47:8000/v1
OPENAI_API_KEY=sk-vllm-17L3d6z60EuhN1yW_bcRoynvDmxoAk1GKsF3QvSV9cY
OPENAI_BASE_URL=http://100.112.53.47:8000/v1
EOF
else
    echo "✅ .env 文件已存在: $ENV_FILE"
fi

# 4. 验证
echo "✅ 环境初始化完成"
echo ""
echo "📋 使用方法:"
echo "  cd /Users/a1-6/Desktop/workspace/tools/memory-benchmarks"
echo "  $VENV_DIR/bin/python -m benchmarks.locomo.smoke_temporal"
