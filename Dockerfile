from debian:jessie
run apt-get update && apt-get install -y \
    python-dev \
    python-pip \
    python-pygresql \
    curl \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
run pip install flask flask-bootstrap sqlalchemy

#************* DEPENDENCIES

copy src/ /app/
run cd /app && python setup.py develop
expose 5000
cmd python -m uservice.api
