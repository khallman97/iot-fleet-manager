# server/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt


# Install wireguard
RUN apt-get update && \
    apt-get install -y wireguard iproute2 iputils-ping && \
    apt-get clean

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8000
ENV FLASK_ENV=development  

RUN chmod +x /app/entrypoint.sh

CMD ["./entrypoint.sh"]