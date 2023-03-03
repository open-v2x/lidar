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

RUN apt-get update && apt-get install -y python3-pip && pip3 install --upgrade pip \
    && apt-get install -y wget

COPY requirements.txt .
RUN pip3 install -r requirements.txt

RUN wget https://openv2x.oss-ap-southeast-1.aliyuncs.com/data/lidar/velo.tar.gz \
    && tar zxvf velo.tar.gz \
    && rm -rf velo.tar.gz


COPY project .
