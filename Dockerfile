FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1


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


RUN python -V && pip install -U pip setuptools wheel


ENV CFLAGS="-D_GNU_SOURCE"
RUN pip install -f https://downloads.openmicroscopy.org/zeroc-ice/3.6/zeroc-ice-cp310/ zeroc-ice==3.6.5
RUN pip install omero-py


RUN pip install napari[all] PyQt5 napari-omero


RUN curl -fsSL https://ollama.com/install.sh | sh


ENV PATH="/usr/local/bin:${PATH}"


RUN pip install \
    "pydantic>=2" requests numpy pandas scikit-learn \
    torch \
    langchain langchain-openai \
    openai \
    huggingface_hub


RUN groupadd -r appuser && useradd -r -g appuser -m appuser


RUN mkdir -p /app && chown -R appuser:appuser /app

ENV DISPLAY=:99 \
    OMERO_HOST=omeroserver \
    OMERO_PORT=4064 \
    PYTHONUNBUFFERED=1 \
    QT_QPA_PLATFORM=xcb \
    QT_X11_NO_MITSHM=1 \
    NUMBA_CACHE_DIR=/tmp/numba_cache


USER appuser

EXPOSE 5901 6080


HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:6080/ || exit 1


COPY container_startup.sh /usr/local/bin/container_startup.sh

CMD ["bash", "/usr/local/bin/container_startup.sh"]