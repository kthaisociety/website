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
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .

ENTRYPOINT ["/website/Docker/entrypoint.sh"]