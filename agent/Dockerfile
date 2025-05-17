FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# Install wireguard
RUN apt-get update && \
    apt-get install -y wireguard iproute2 iputils-ping && \
    apt-get clean

CMD ["python", "agent.py"]
