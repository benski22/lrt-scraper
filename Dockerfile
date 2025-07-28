FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

# Kad logai būtų rodomi realiu laiku
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
