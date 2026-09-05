FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN wget -q https://github.com/skylot/jadx/releases/latest/download/jadx-1.5.3.zip -O jadx.zip \
    && unzip jadx.zip -d /opt/jadx \
    && rm jadx.zip

ENV PATH="/opt/jadx/bin:${PATH}"

COPY . .

CMD ["python", "bot.py"]
