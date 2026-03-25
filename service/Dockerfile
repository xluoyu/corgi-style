FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# Railway 暴露端口
ENV PORT=8000
EXPOSE 8000

# Railway 启动
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
