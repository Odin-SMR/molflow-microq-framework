from debian:jessie
copy requirements.txt /tmp/
run apt-get update && apt-get install -y \
    python-dev \
    python-pip && \
    pip install -r /tmp/requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

copy src/ /app/
expose 5000
workdir /app
cmd gunicorn -w 4 -k gevent -b 0.0.0.0:5000 uservice.core.app:app
