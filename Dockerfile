FROM ubuntu:22.04

WORKDIR /app

# 安装 Python3 和 pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 uv 和项目依赖
COPY requirements.txt ./
RUN pip3 install uv && \
    uv pip install --system --no-cache -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 复制应用源码
COPY . .

# 暴露应用端口
EXPOSE 7860

# 启动应用
CMD ["python3", "app.py"]
