FROM python:3.10.12-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install git build-essential gdal-bin libgdal-dev -y

COPY . .

RUN pip install cython && \
    pip install -e . && \
    pip install gunicorn && \
    pip install pymysql && \
    pip install terracotta==0.8.2

CMD ["gunicorn", "terracotta.server.app:app", "--bind", "0.0.0.0:5000"]