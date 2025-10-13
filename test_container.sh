#!/bin/bash

echo "Testing Docker container setup..."

# 检查容器是否正在运行
if docker ps | grep -q llm-agent-test; then
    echo "✅ Container is running"
    
    # 检查端口是否开放
    if curl -s http://localhost:6080 > /dev/null; then
        echo "✅ noVNC web interface is accessible at http://localhost:6080"
    else
        echo "❌ noVNC web interface is not accessible"
    fi
    
    if nc -z localhost 5901; then
        echo "✅ VNC server is running on port 5901"
    else
        echo "❌ VNC server is not accessible"
    fi
    
    echo ""
    echo "🎉 Container is working! You can access the Napari GUI at:"
    echo "   http://localhost:6080"
    echo ""
    echo "To stop the container, run:"
    echo "   docker stop llm-agent-test"
    
else
    echo "❌ Container is not running"
    echo "To start the container, run:"
    echo "   docker run --rm --name llm-agent-test -p 6080:6080 -p 5901:5901 -e OPENAI_API_KEY=test -v \"$(pwd)/llm-agent:/app\" llm-agent"
fi
