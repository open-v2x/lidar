FROM ubuntu:22.04

WORKDIR /lidar

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt update && apt install -y python3-pip && pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip
COPY requirements.txt .
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY project .
