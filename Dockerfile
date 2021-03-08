FROM python:3.8-alpine

WORKDIR /usr/local/bin/subtocall

# Copy only requirements file
COPY ./requirements.txt .

# Install build dependencies
RUN apk update \
    && apk add --no-cache git \
    && apk add --no-cache --virtual .build-deps libressl-dev musl-dev libffi-dev gcc g++ rust cargo python3-dev\
    && pip install --no-cache-dir -r requirements.txt \
    && apk del --no-cache .build-deps

# Copy authserver files to container /usr/local/bin/subtocall
COPY . .

# Disable colored logs as they make parsing very hard
ENV COLORED_LOGS false

# Run authserver
CMD ["python", "-m", "subtocall.main"]