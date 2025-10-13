# OMERO.server and OMERO.web with Napari LLM Agent (docker-compose)

This is an example of running OMERO.server, OMERO.web, and a Napari LLM Agent in Docker.

## Quick Overview of Containers 

- **OMERO.server**: Listening on ports `4063` and `4064`
- **OMERO.web**: Available at http://localhost:8080/
- **Napari LLM Agent**: Available via noVNC at http://localhost:6080/
- **VNC Server**: Direct connection at localhost:5901

Log in as user `root` password `omero`.
The initial password can be changed in [`docker-compose.yml`](docker-compose.yml).


## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key
- At least 4GB of available RAM
- Ports 6080, 5901, 8080, 4063, 4064 available


##  Instruction for Container Setup

### 1. Set up environmental variables

Each team member needs to set up their own API keys and create the `.env` file:
The `env.example` file serves as a template 

1. **Copy the example environment file:**
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` and add your OpenAI API key:**
   ```bash
   OPENAI_API_KEY=your_actual_api_key_here
   ```


### 2. Set up and run containers

1. **Make the script executable:**
   ```bash
   chmod +x start_llm_agent.sh
   ```

2. **Run the startup script:**
   ```bash
   ./start_llm_agent.sh
   ```



### 3. Connect to Napari via Linux GUI within the container


### (1). Napari GUI (Main Interface)

1. **Open your browser** and go to: http://localhost:6080
2. **You'll see a file listing** - click on **`vnc_auto.html`**
3. **The VNC client will load** and connect to the Napari GUI
4. **You should see the Napari interface** with LLM integration

### Optional: (2). OMERO Web Interface

- **URL**: http://localhost:8080
- **Login**: username `root`, password `omero`

### Optional: (3). Direct VNC Connection

- **Host**: localhost
- **Port**: 5901
- **Use any VNC client** (like RealVNC, TightVNC, etc.)




##  Stopping the Application

### Method 1: Using the Script
- Press `Ctrl+C` in the terminal where the script is running
- Then run: `docker compose -f docker-compose.yml -f docker-compose-override.yml down`

### Method 2: Manual Stop
```bash
docker compose -f docker-compose.yml -f docker-compose-override.yml down
```