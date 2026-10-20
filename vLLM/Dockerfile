FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY L3_fastAPI.py .

EXPOSE 3002

CMD ["uvicorn", "L3_fastAPI:app", "--host", "0.0.0.0", "--port", "3002"]