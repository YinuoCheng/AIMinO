#!/bin/bash

echo " Starting Napari LLM Agent with OMERO..."


if [ ! -x "$0" ]; then
    echo " Setting up script permissions..."
    chmod +x "$0"
    chmod +x container_startup.sh
fi


if [ ! -f .env ]; then
    echo " .env file not found!"
    echo "Please create a .env file with your OpenAI API key:"
    echo "   cp env.example .env"
    echo "   # Then edit .env and add your OPENAI_API_KEY"
    exit 1
fi



echo " Environment configuration looks good"


echo " Cleaning up previous containers..."
docker compose -f docker-compose.yml -f docker-compose-override.yml down 2>/dev/null


echo " Building LLM Agent image..."
docker buildx build --platform linux/amd64 -t llm-agent -f Dockerfile .


echo " Starting OMERO services in background..."
docker compose -f docker-compose.yml -f docker-compose-override.yml up -d database omeroserver omeroweb


echo " Waiting for OMERO services to start..."
sleep 10


echo " Starting LLM Agent in foreground..."
echo " Container will start in /app directory as specified in Dockerfile"
docker compose -f docker-compose.yml -f docker-compose-override.yml --profile gui up llm-agent

echo " Napari LLM Agent is now running!"
echo "   Web interface: http://localhost:6080"
echo "   VNC server: localhost:5901"
echo "   OMERO Web: http://localhost:8080"
echo ""
echo "To stop all services, press Ctrl+C or run:"
echo "   docker compose -f docker-compose.yml -f docker-compose-override.yml down"
