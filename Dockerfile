from debian:jessie
run apt-get update && apt-get install -y \
    python-dev \
    python-pip \
    python-pygresql \
    python-psycopg2 \
    curl \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
run pip install flask flask-bootstrap flask-httpauth flask-restful \
    passlib flask-sqlalchemy sqlalchemy pymysql

#************* DEPENDENCIES

copy src/ /app/
run cd /app && python setup.py develop
expose 5000
copy start.py /start.py
cmd python /start.py
