FROM python:3.8
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
COPY src/ /app/
EXPOSE 5000
WORKDIR /app
CMD gunicorn -w 4 -k gevent -b 0.0.0.0:5000 --timeout 300 uservice.core.app:app
