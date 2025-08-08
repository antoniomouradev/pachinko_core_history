FROM python:3.13-bullseye

WORKDIR /app

COPY app/ .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["sh", "-c", "python app.py"]
