ARG BUILD_TARGET=dev
LABEL org.opencontainers.image.source https://github.com/kthaisociety/website

# Base docker used. This one will use the latest version of python.
FROM python:3.9

# Extra Python environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1
# Use Python binaries from venv
ENV PATH="/website/venv/bin:$PATH"


# Pinned versions
ENV PIP_PIP_VERSION 22.1
ENV PIP_PIP_TOOLS_VERSION 6.6.0
ENV APT_NETCAT_VERSION 1.10-46
ENV APT_CHROMIUM_VERSION 99.0.4844.74-1~deb11u1
ENV APT_FONTS_NOTO_COLOR_EMOJI_VERSION 0~20200916-1

# Install sys dependencies
RUN apt update && apt install -y --no-install-recommends \
      "netcat=$APT_NETCAT_VERSION"  \
      "chromium=$APT_CHROMIUM_VERSION" \
      "chromium-common=$APT_CHROMIUM_VERSION" \
      "fonts-noto-color-emoji=$APT_FONTS_NOTO_COLOR_EMOJI_VERSION" \
    && apt clean \
 	&& rm -rf "/var/lib/apt/lists/*"
# Setup the virtualenv
RUN python -m venv /website/venv
WORKDIR /website

# Install Python dependencies
COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt
ARG BUILD_TARGET

RUN set -x && pip install pip==$PIP_PIP_VERSION pip-tools==$PIP_PIP_TOOLS_VERSION && \
    pip install --pre -r "requirements.txt" && \
    if [ "${BUILD_TARGET}" = "dev" ] ; then \
        pip install --pre -r "requirements-dev.txt" ; \
    fi && \
    pip check

# app user
RUN groupadd -r app -g 1000 && useradd -r -g app -u 1000 app -d /website
RUN chown -R app:app /website

USER app
COPY . .

# Run entrypoint
ENTRYPOINT ["/website/Docker/entrypoint.sh", "python", "manage.py", "runserver", "0.0.0.0:80"]
