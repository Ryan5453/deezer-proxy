FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update 
RUN apt-get install -y python3.9 python3-pip
RUN apt-get clean 
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy requirements to app dir so it can be cached
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy the source code
COPY ./ /app/

WORKDIR /app

ENTRYPOINT uvicorn deezer:app --host 0.0.0.0 --port 9999