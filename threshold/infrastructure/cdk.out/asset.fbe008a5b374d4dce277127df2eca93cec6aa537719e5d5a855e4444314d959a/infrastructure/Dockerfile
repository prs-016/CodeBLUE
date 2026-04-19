FROM node:20-bookworm-slim
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv zip unzip
RUN npm install -g aws-cdk
WORKDIR /app/infrastructure
COPY infrastructure/requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt --break-system-packages
