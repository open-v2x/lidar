FROM ubuntu:22.04

WORKDIR /lidar

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt update && apt install -y python3-pip && pip3 install --upgrade pip \
    && apt-get install -y wget

COPY requirements.txt .
RUN pip3 install -r requirements.txt

RUN wget https://openv2x.oss-ap-southeast-1.aliyuncs.com/data/lidar/lid23D.cap.tar.gz \
    && tar zxvf lid23D.cap.tar.gz \
    && rm -rf lid23D.cap.tar.gz

COPY project .
