FROM python:3.8-alpine

# Install build dependencies
RUN apk add --no-cache libressl-dev
RUN apk add --virtual .build_deps --no-cache gcc libffi-dev musl-dev python3-dev

WORKDIR /usr/local/bin/subtocall

# Copy only requirements file
COPY ./requirements.txt .

# Install python dependenices
RUN pip install -r requirements.txt

# We can remove the build dependencies again
RUN apk del .build_deps

# Copy authserver files to container /usr/local/bin/subtocall
COPY . .

# Disable colored logs as they make parsing very hard
ENV COLORED_LOGS false

# Run authserver
CMD ["python", "main.py"]