FROM node:20-bookworm-slim
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv zip unzip ca-certificates curl
RUN install -m 0755 -d /etc/apt/keyrings && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && chmod a+r /etc/apt/keyrings/docker.asc
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update && apt-get install -y docker-ce-cli
RUN npm install -g aws-cdk
WORKDIR /app/infrastructure
COPY infrastructure/requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt --break-system-packages
