FROM python:3.11-slim-buster

ENV PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Fix sources.list and install packages
RUN sed -i 's/http:\/\/deb.debian.org/http:\/\/archive.debian.org/g' /etc/apt/sources.list && \
    apt-get update && apt-get upgrade -y && \
    apt-get install --no-install-recommends -y \
    bash \
    bzip2 \
    curl \
    figlet \
    git \
    libffi-dev \
    libjpeg62-turbo-dev \
    libwebp-dev \
    musl-dev \
    neofetch \
    python3-lxml \
    python3-pip \
    python3-requests \
    python3-aiohttp \
    openssl \
    wget \
    python3-dev \
    gcc \
    zlib1g-dev \
    ffmpeg \
    libssl-dev \
    libopus0 \
    libopus-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools
RUN python3 -m pip install --upgrade pip setuptools wheel

# Clone repository and set working directory
COPY . /app/
WORKDIR /app

# Install Python requirements
RUN pip3 install --no-cache-dir -U -r requirements.txt

# Set environment variables
ENV PYTHONPATH=/app \
    PATH="/app/bin:$PATH"

# Run the application
CMD ["python3", "-m", "shivu"]
