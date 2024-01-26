FROM python:3.10

RUN apt-get update && apt install build-essential gdal-bin libgdal-dev -y

COPY . .

RUN pip install cython && \
    pip install -e . && \
    pip install gunicorn

CMD ["gunicorn", "terracotta.server.app:app", "--bind", "0.0.0.0:5000"]