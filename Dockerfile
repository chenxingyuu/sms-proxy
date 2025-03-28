# 使用官方的 Python 基础镜像
FROM python:3.12.9-slim
LABEL authors="chenxingyu"

# 安装 tzdata 包以设置时区
RUN apt-get update && \
    apt-get install -y tzdata gcc && \
    rm -rf /var/lib/apt/lists/*

# 设置时区环境变量（例如：Asia/Shanghai）
ENV TZ=Asia/Shanghai

# 设置工作目录
WORKDIR /app

# 安装所需的 Python 包
COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 将当前目录内容复制到 /app 目录
COPY . /app

# 设置 PYTHONPATH 环境变量
ENV PYTHONPATH="${PYTHONPATH}:/app/"

# 运行主程序
CMD ["python", "main.py"]
