# 使用官方 Python 鏡像作為基礎
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 複製當前目錄內容到容器的 /app 目錄
COPY . /app

# 安裝所需的 Python 包
RUN pip install --no-cache-dir -r requirements.txt

# 設置環境變量
ENV FLASK_APP=main.py

# 暴露端口
EXPOSE 8000

# 運行 Flask 應用
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "main:app"]