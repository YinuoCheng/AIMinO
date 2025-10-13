#!/bin/bash

echo "🚀 Starting Napari LLM Agent with OMERO..."

# 检查 .env 文件是否存在
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with your OpenAI API key:"
    echo "   cp env.example .env"
    echo "   # Then edit .env and add your OPENAI_API_KEY"
    exit 1
fi

# 检查 API key 是否设置
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "❌ OPENAI_API_KEY not properly set in .env file!"
    echo "Please edit .env and add your actual OpenAI API key"
    exit 1
fi

echo "✅ Environment configuration looks good"

# 停止并清理之前的容器
echo "🧹 Cleaning up previous containers..."
docker compose -f docker-compose.yml -f docker-compose-override.yml down 2>/dev/null

# 构建 LLM Agent 镜像（如果需要）
echo "🔨 Building LLM Agent image..."
docker buildx build --platform linux/amd64 -t llm-agent -f Dockerfile .

# 启动后台服务（OMERO 相关）
echo "📦 Starting OMERO services in background..."
docker compose -f docker-compose.yml -f docker-compose-override.yml up -d database omeroserver omeroweb

# 等待后台服务启动
echo "⏳ Waiting for OMERO services to start..."
sleep 10

# 启动 LLM Agent 在前台，并进入 /app 文件夹
echo "🤖 Starting LLM Agent in foreground..."
echo "📁 Container will start in /app directory as specified in Dockerfile"
docker compose -f docker-compose.yml -f docker-compose-override.yml --profile gui up llm-agent

echo "🎉 Napari LLM Agent is now running!"
echo "   Web interface: http://localhost:6080"
echo "   VNC server: localhost:5901"
echo "   OMERO Web: http://localhost:8080"
echo ""
echo "To stop all services, press Ctrl+C or run:"
echo "   docker compose -f docker-compose.yml -f docker-compose-override.yml down"
