FROM nvidia/cuda:11.3.0-cudnn8-devel-ubuntu18.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/root/OpenPCDet:$PYTHONPATH

# To fix GPG key error when running apt-get update
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64/7fa2af80.pub

# Install basics
RUN apt-get update -y \
    && apt-get install build-essential \
    && apt-get install -y vim apt-utils apt-transport-https git curl ca-certificates bzip2 tree htop wget gnupg ninja-build cmake\
    && apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev libboost-dev libgl1-mesa-glx bmon iotop g++ python3.8 python3.8-dev python3.8-distutils

# Install python
RUN ln -sv /usr/bin/python3.8 /usr/bin/python
RUN wget https://bootstrap.pypa.io/get-pip.py && \
	python get-pip.py && \
	rm get-pip.py

# Install torch and torchvision
# See https://pytorch.org/ for other options if you use a different version of CUDA
RUN pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 -f https://download.pytorch.org/whl/torch_stable.html

# Install python packages
RUN pip install numpy llvmlite numba tensorboardX easydict pyyaml scikit-image tqdm six

WORKDIR /root

# Install Boost geometry
RUN wget https://jaist.dl.sourceforge.net/project/boost/boost/1.68.0/boost_1_68_0.tar.gz && \
    tar xzvf boost_1_68_0.tar.gz && \
    cp -r ./boost_1_68_0/boost /usr/include && \
    rm -rf ./boost_1_68_0 && \
    rm -rf ./boost_1_68_0.tar.gz 

RUN pip install spconv-cu113

ARG TORCH_CUDA_ARCH_LIST="5.2 6.0 6.1 7.0 7.5+PTX"

COPY openpcdet /root/OpenPCDet/

RUN cd /root/OpenPCDet &&\
    pip install -r requirements.txt &&\
    python setup.py develop

WORKDIR /root/OpenPCDet/
# RUN echo 'export PYTHONPATH=/root/OpenPCDet:$PYTHONPATH' >>~/.bashrc

EXPOSE 28300

CMD ["sh", "/root/OpenPCDet/start.sh"]