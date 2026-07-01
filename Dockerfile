FROM dhi.io/python:3.11-dev AS builder

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/src/app/venv/bin:$PATH"

WORKDIR /usr/src/app

RUN python -m venv ./venv
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM dhi.io/python:3.11

WORKDIR /usr/src/app

ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/src/app/venv/bin:$PATH"

COPY ./src ./src
COPY ./newrelic_sample.ini ./newrelic.ini

COPY --from=builder /usr/src/app/venv ./venv

ENTRYPOINT [ "python", "./src/__main__.py" ]
