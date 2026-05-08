FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir --no-compile -r requirements.txt \
    && find /usr/local/lib/python3.11 -type f -name '*.pyc' -delete \
    && find /usr/local/lib/python3.11 -depth -type d -name '__pycache__' -exec rm -rf {} +

COPY . .

CMD ["python", "scheduler.py"]
