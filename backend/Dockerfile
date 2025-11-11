FROM python:3.11-slim

WORKDIR /app

# Install base packages
RUN apt-get update && apt-get install -y --no-install-recommends build-essential ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip toolchain
RUN pip install --upgrade pip setuptools wheel packaging

# Copy and install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY app /app

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

