FROM ubuntu:22.04

WORKDIR /lidar

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt update && apt install -y python3-pip && pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip \
    && apt-get install -y wget
COPY requirements.txt .
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

RUN wget https://openv2x.oss-ap-southeast-1.aliyuncs.com/deploy/lidar/lid23D.cap

COPY project .