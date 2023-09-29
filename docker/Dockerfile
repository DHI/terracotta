FROM python:3.10.12-slim-bullseye as build_tarball

RUN apt-get update \
    && apt-get install \
    -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY ./ /terracotta
COPY ./docker/entrypoint.sh /entrypoint.sh

WORKDIR /terracotta

RUN python -m pip install --upgrade pip \
    && python setup.py sdist


FROM python:3.10.12-slim-bullseye

COPY --from=build_tarball /terracotta/dist/terracotta-*.tar.gz /terracotta/terracotta.tar.gz

RUN pip install --upgrade pip \
    && pip install psycopg2-binary gunicorn \
    && pip install /terracotta/terracotta.tar.gz \
    && rm -rf /terracotta

COPY --from=build_tarball /entrypoint.sh /entrypoint.sh

ENV TC_SERVER_PORT=5000
EXPOSE $TC_SERVER_PORT

CMD ["/entrypoint.sh"]
