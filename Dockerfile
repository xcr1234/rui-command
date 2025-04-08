# 使用官方 Python 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将当前目录的文件复制到容器中
COPY . .

# 安装依赖
RUN pip install  -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# 暴露应用运行的端口（根据你的应用配置）
EXPOSE 8101

# 启动命令
CMD ["python", "bot.py"]