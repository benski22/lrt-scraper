FROM mcr.microsoft.com/playwright/python:v1.42.0

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
