# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py /app/

EXPOSE 8000

ENV MODEL_INPUT_NAME=input:0
ENV MODEL_OUTPUT_NAME=
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

