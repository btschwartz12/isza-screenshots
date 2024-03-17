FROM python:3.11-slim

WORKDIR /app

COPY . ./

# install sqlite3
RUN apt-get update && apt-get install -y sqlite3

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000