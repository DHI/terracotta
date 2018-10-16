FROM python:3.6-slim

USER root

ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

SHELL ["bash", "-l", "-c"]

RUN python3 -m ensurepip && \
    pip3 install --upgrade pip setuptools && \
    pip3 install virtualenv && \
    virtualenv /env/tc-deploy --python=python3

COPY package/remote_requirements.txt /tmp/requirements.txt
RUN source /env/tc-deploy/bin/activate && \
    pip install -r /tmp/requirements.txt --only-binary rasterio && \
    pip install zappa

COPY . /terracotta
ENV PYTHONPATH='/terracotta'
WORKDIR /terracotta

COPY package/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]