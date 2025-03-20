FROM python:3.9

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src
COPY ./newrelic_sample.ini ./newrelic.ini

ENTRYPOINT [ "python3", "./src/__main__.py" ]
