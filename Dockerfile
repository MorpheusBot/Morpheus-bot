FROM python:3.13-alpine3.21

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update && apk add git
WORKDIR /morpheus
RUN mkdir -p /morpheus/logs

# Install python dependencies
RUN /usr/local/bin/python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

RUN git config --global --add safe.directory /morpheus

ENTRYPOINT [ "python3", "morpheus.py" ]
