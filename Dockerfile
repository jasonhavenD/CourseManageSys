# Dockerfile - this is a comment. Delete me if you want.
FROM openjdk:8-jre
FROM python:3.6

WORKDIR /app
COPY . /app

# 安装依赖
RUN pip install -r requirements.txt

CMD [ "python", "client.py" ]
