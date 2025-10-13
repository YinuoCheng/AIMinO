FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 运行库 & 构建工具（napari + 科学计算常用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential g++ curl git \
    xvfb x11vnc fluxbox websockify novnc \
    libgl1-mesa-dri libglib2.0-0 libxkbcommon0 libxrender1 libxcomposite1 \
    libxi6 libxtst6 libxrandr2 libxext6 libfontconfig1 libfreetype6 \
    libbz2-dev zlib1g-dev libssl-dev \
    libc6-dev linux-libc-dev \
    libxcb1 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-util1 libxcb-xfixes0 \
    libqt5gui5 libqt5widgets5 libqt5core5a libqt5dbus5 \
    && rm -rf /var/lib/apt/lists/*

# 升级打包工具
RUN python -V && pip install -U pip setuptools wheel

# 安装 OMERO 相关包 - 设置编译标志解决 readlink 问题
ENV CFLAGS="-D_GNU_SOURCE"
RUN pip install -f https://downloads.openmicroscopy.org/zeroc-ice/3.6/zeroc-ice-cp310/ zeroc-ice==3.6.5
RUN pip install omero-py

# 安装 napari 和必要的 Qt 绑定，以及 OMERO 集成
RUN pip install napari[all] PyQt5 napari-omero

# 其余依赖分步装，更容易看出出错点
RUN pip install \
    "pydantic>=2" requests numpy pandas scikit-learn \
    torch \
    langchain langchain-openai \
    openai

# 创建非 root 用户和主目录
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

WORKDIR /app

# 设置目录权限
RUN chown -R appuser:appuser /app

ENV DISPLAY=:99 \
    OMERO_HOST=omeroserver \
    OMERO_PORT=4064 \
    PYTHONUNBUFFERED=1 \
    QT_QPA_PLATFORM=xcb \
    QT_X11_NO_MITSHM=1 \
    NUMBA_CACHE_DIR=/tmp/numba_cache

# 切换到非 root 用户
USER appuser

EXPOSE 5901 6080

# 添加健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:6080/ || exit 1

CMD bash -lc '\
      echo "Setting up permissions..." && \
      mkdir -p /tmp/.X11-unix && \
      chmod 1777 /tmp/.X11-unix && \
      echo "Cleaning up previous X server..." && \
      rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 && \
      echo "Starting X server..." && \
      Xvfb :99 -screen 0 1600x900x24 -ac +extension GLX +render -noreset & \
      sleep 3 && \
      echo "Starting window manager..." && \
      fluxbox & \
      sleep 2 && \
      echo "Starting VNC server..." && \
      x11vnc -display :99 -forever -nopw -rfbport 5901 & \
      sleep 2 && \
      echo "Starting noVNC web server..." && \
      websockify --web=/usr/share/novnc 6080 localhost:5901 & \
      sleep 2 && \
      echo "Starting napari LLM application..." && \
      if [ -f /app/napariLLM.py ]; then \
        python /app/napariLLM.py; \
      else \
        echo "Warning: napariLLM.py not found, starting napari instead" && \
        napari; \
      fi \
    '