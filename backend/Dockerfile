FROM python:3.12-slim

WORKDIR /app

# Install system dependencies: Docker CLI, Git, OpenSSH, procps, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    docker.io \
    git \
    procps \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
