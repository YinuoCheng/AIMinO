# Omero Napari LLM Agent 


## Quick Overview of Containers 

- **OMERO.server**: Listening on ports `4063` and `4064`
- **OMERO.web**: Available at http://localhost:8080/
- **Napari LLM Agent**: Available via noVNC at http://localhost:6080/
- **Database**:

Log in as user `root` password `omero`


##  Instruction for Container Setup

### 1. Set up environmental variables

Each person needs to set up their own API keys and create the `.env` file:
The `env.example` file serves as a template 

1. **Copy the example environment file:**
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` and add your LLM API key:**
   ```bash
   HF_TOKEN=your_huggingface_token_here
   ```


### 2. Set up and run containers

```bash
bash start_llm_agent.sh
```


### 3. Connect to Napari via Linux GUI within the container

1. **Open your browser** and go to: http://localhost:6080/vnc_auto.html
The VNC client will load and connect to the Napari GUI, and you should see the Napari interface** with LLM integration

```