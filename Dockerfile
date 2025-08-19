FROM python:3.11-slim-buster

ENV PIP_NO_CACHE_DIR 1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/
RUN python3 -m pip install --upgrade pip setuptools
RUN pip3 install -U -r requirements.txt

ENV PATH="/home/bot/bin:$PATH"

# Starting Worker
CMD ["python3","-m", "shivu"]
