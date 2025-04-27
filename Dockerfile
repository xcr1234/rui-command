# 使用官方 Python 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装 git
RUN apt-get install -y git

# 删除 /fortune 目录（如果存在）
RUN rm -rf /fortune

# 克隆仓库到 /fortune 目录（这个里面有项目需要的资源文件），只克隆最新一次提交
RUN git clone --depth 1 https://github.com/MinatoAquaCrews/nonebot_plugin_fortune.git /fortune


# 将当前目录的文件复制到容器中
COPY . .

# 安装依赖
RUN pip install --no-cache-dir  -r requirements.txt

# 暴露应用运行的端口（根据你的应用配置）
EXPOSE 8101

# 启动命令
CMD ["python", "bot.py"]