FROM python:3.12-alpine

RUN apk add --no-cache ripgrep \
    && pip install --no-cache-dir pyyaml==6.0.2

WORKDIR /src
COPY k6t-lint k6t-lint.yaml /opt/k6t-lint/
COPY scripts /opt/k6t-lint/scripts
RUN chmod +x /opt/k6t-lint/k6t-lint /opt/k6t-lint/scripts/domain-consts.py

ENTRYPOINT ["/opt/k6t-lint/k6t-lint"]
