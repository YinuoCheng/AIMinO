# AC215 - Milestone2 - Agentic AI for Conversational Imaging Control and Cell Type Modeling with OMERO (AIMinO)

## Team Members
Yingxiao Shi (TK), Chung-Ta Huang (Kida), Yinuo Cheng, Yuan Tian

## Group Name
AIMinO

## Project
In this project, we aim to develop an AI-powered imaging analysis application called AIMinO (Agentic AI for Conversational Imaging Control and Cell Type Modeling with OMERO). The application will feature conversational AI agents that can control imaging software (Napari) through natural language commands and perform cell type annotation and analysis. Users can interact with the system through a chat interface to request various imaging operations, data analysis, and cell type identification tasks. The system integrates with OMERO for data management and uses LLM agents to process user requests and generate executable commands for imaging software, making it a powerful tool for multiplexing image analysis and biomedical research.

---

# Milestone2 
In this milestone, we have set up the LLM agent container, which is the major component of the agentic AI pipeline for multiplexing imaging control and analysis. 

---

# Data
The sample analyzed in this study was obtained from a patient with metastatic melanoma who initially responded to immunotherapy and maintained stable disease for 12 years before tumor resection. Notably, the resected tumor still contained proliferating tumor cells without evidence of progression. We performed multiplex immunofluorescence staining using markers for both tumor and non-tumor cell populations to investigate the biological mechanisms underlying this prolonged stability. This approach aims to characterize tumor–immune interactions that may contribute to the non-progressive state of the disease.

For pipeline testing, we selected a smaller region of the tumor to generate a reduced-size TIFF file. Segmentation was performed using MCMICRO, which produced a corresponding .csv datatable containing single-cell measurements for downstream analysis.

For detailed description of the imaging data, please refer to Data description file in data folder.

---

## Quick Overview of Containers 

### **Napari LLM Agent**  Available via noVNC at http://localhost:6080/
- This is the main container that serves as the core of the AIMinO system. It contains Napari, a viewer for multiplexing image analysis, together with LLM agent that processes user requests and generates executable commands for Napari. Users can access to the Napari GUI through VNC and enter specific requests to visualize and analyze the multiplexing images. The LLM component will translate user requests into actions in json format, and the agent will then evaluate and process this output from LLM to generate executable commands to control Napari. This pipeline allows researchers to manage complex imaging workflows through natural language interaction, enabling advanced multiplexed image analysis with simple, conversational commands.

### **OMERO.server** Access: Listening on ports `4063` and `4064`
- This is the one of the components of the OMERO system that provides image data storage and management services through its connection to the PostgreSQL database. It acts as a gate that allows users to store and retrieve biomedical imaging data for analysis. 

### **OMERO.web**  Access: Available at http://localhost:8080/
- This is the web-based user interface component of the OMERO system that allows users to access to OMERO functionality, which includes image viewing and annotation tools. 

### **Database**
- This is the PostgreSQL database connected to OMERO server, and it is responsible for the storage of multiplexing image data, cell metadata, and annotations for analysis. 

---

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



---

# Description of coding files

**src/Dockerfile**: This dockerfile defines the container image configuration for LLM agent container, including all necessary dependencies and environment setup.

**src/llm-agent/napariLLM.py**: This is the core Python script that implements the LLM agent functionality for processing natural language requests from users and generating Napari commands.

**src/docker-compose.yml**: Main Docker compose configuration file that defines all services (Napari LLM Agent, OMERO.server, OMERO.web, and Database) and their networking.

**src/docker-compose-override.yml**: Docker compose configuration file that sets up the LLM-agent container, the main component of our agentic AI pipeline.

**src/env.example**: Users can copy this template file and enter their API keys for LLM.

**src/start_llm_agent.sh**: Shell script that automates the startup process for the entire AIMinO system using Docker Compose.

**src/container_startup.sh**: Container initialization script that handles the setup and configuration of services within the Docker containers.

