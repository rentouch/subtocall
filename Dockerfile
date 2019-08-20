FROM ubuntu:18.04

# Install pip and virtualenv
RUN apt-get update && apt-get install -y python3 curl python3-distutils
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3 get-pip.py
RUN pip3 install virtualenv

WORKDIR /usr/local/bin/subtocall

# Copy only requirements file
COPY ./requirements.txt .

# Create virtualenv
RUN virtualenv -p python3 venv
RUN venv/bin/pip install -r requirements.txt

# Copy authserver files to container /usr/local/bin/subtocall
COPY . .

# Disable colored logs as they make parsing very hard
ENV COLORED_LOGS false

# Run authserver
CMD ["venv/bin/python", "main.py"]