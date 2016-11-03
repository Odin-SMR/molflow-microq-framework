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

run pip install aniso8601==1.2.0          # via flask-restful
run pip install click==6.6                # via flask
run pip install ConcurrentLogHandler==0.9.1
run pip install dominate==2.2.1           # via flask-bootstrap
run pip install flask-bootstrap==3.3.7.0
run pip install flask-httpauth==3.2.1
run pip install flask-restful==0.3.5
run pip install flask-sqlalchemy==2.1
run pip install Flask==0.11.1             # via flask-bootstrap, flask-httpauth, flask-restful, flask-sqlalchemy
run pip install functools32==3.2.3-2  # via jsonschema
run pip install itsdangerous==0.24        # via flask
run pip install Jinja2==2.8               # via flask
run pip install jsl==0.2.4
run pip install jsonschema==2.5.1
run pip install MarkupSafe==0.23          # via jinja2
run pip install passlib==1.6.5
run pip install pymysql==0.7.9
run pip install python-dateutil==2.5.3
run pip install pytz==2016.7              # via flask-restful
run pip install six==1.10.0               # via flask-restful, python-dateutil
run pip install sqlalchemy==1.1.3
run pip install visitor==0.1.3            # via flask-bootstrap
run pip install Werkzeug==0.11.11         # via flask

copy src/ /app/
run cd /app && python setup.py develop
expose 5000
copy start.py /start.py
cmd python /start.py
