FROM python:3.9-slim-buster

WORKDIR /app

COPY main.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["python", "main.py"]