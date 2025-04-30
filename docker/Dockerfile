FROM python:3.13.3-slim-bullseye AS build_wheel

RUN apt-get update \
    && apt-get install \
    -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY ./ /terracotta

WORKDIR /terracotta

RUN python -m pip install --upgrade pip \
    && python setup.py bdist_wheel


FROM python:3.13.3-slim-bullseye

COPY --from=build_wheel /terracotta/dist/*.whl /terracotta/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        $(ls /terracotta/*.whl) \
        pymysql>=1.0.0 \
        psycopg2-binary \
        gunicorn \
        werkzeug==0.16.0 \
        markupsafe==2.0.1 \
    && rm -rf /terracotta

COPY docker/resources /

ENV TC_SERVER_PORT=5000
EXPOSE $TC_SERVER_PORT

CMD ["/entrypoint.sh"]
