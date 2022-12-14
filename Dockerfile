FROM ubuntu:22.04

ARG GIT_BRANCH
ARG GIT_COMMIT
ARG RELEASE_VERSION
ARG REPO_URL

LABEL lidar.build_branch=${GIT_BRANCH} \
      lidar.build_commit=${GIT_COMMIT} \
      lidar.release_version=${RELEASE_VERSION} \
      lidar.repo_url=${REPO_URL}

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
