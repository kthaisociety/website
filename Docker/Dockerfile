# Base docker used. This one will use the latest version of python.
FROM python:3.9

# Setting up the work directory
WORKDIR /website

RUN apt-get update && apt install -y netcat

## set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip

# Copy repository to the work directory
RUN git clone https://github.com/kthaisociety/website.git .

# Install requirements
RUN pip install -r requirements.txt

RUN mkdir -p Docker
COPY ./entrypoint.sh ./Docker/entrypoint.sh

# Run entrypoint
ENTRYPOINT ["/website/Docker/entrypoint.sh", "python3", "manage.py", "runserver", "0.0.0.0:80"]
