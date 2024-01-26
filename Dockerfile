FROM python:3.12.1-slim-bookworm

RUN apt-get update && apt-get install git build-essential gdal-bin libgdal-dev -y

COPY . .

RUN pip install cython && \
    pip install -e . && \
    pip install gunicorn

CMD ["gunicorn", "terracotta.server.app:app", "--bind", "0.0.0.0:5000"]