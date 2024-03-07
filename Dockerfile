FROM ghcr.io/osgeo/gdal:alpine-small-latest

# For opencontainers label definitions, see:
#    https://github.com/opencontainers/image-spec/blob/master/annotations.md
LABEL org.opencontainers.image.title="Harmony OPERA RTC Reproject"
LABEL org.opencontainers.image.description="Reproject OPERA RTC"
LABEL org.opencontainers.image.vendor="Alaska Satellite Facility"
LABEL org.opencontainers.image.authors="tools-bot <UAF-asf-apd@alaska.edu>"
LABEL org.opencontainers.image.licenses="BSD-3-Clause"
LABEL org.opencontainers.image.url="https://github.com/ASFHyP3/harmony-opera-rtc-reproject"
LABEL org.opencontainers.image.source="https://github.com/ASFHyP3/harmony-opera-rtc-reproject"
LABEL org.opencontainers.image.documentation="https://hyp3-docs.asf.alaska.edu"

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=true

RUN apt-get update && apt-get install -y --no-install-recommends unzip vim && \
    apt-get clean && rm -rf /var/lib/apt/lists/* \

RUN apk add bash build-base gcc g++ gfortran openblas-dev cmake python3 python3-dev libffi-dev netcdf-dev libxml2-dev libxslt-dev libjpeg-turbo-dev zlib-dev hdf5 hdf5-dev gdal-dev gdal-tools

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip3 install gdal numpy netCDF4 matplotlib harmony-service-lib

# Create a new user
RUN adduser -D -s /bin/sh -h /home/dockeruser -g "" -u 1000 dockeruser
USER dockeruser
ENV HOME /home/dockeruser

USER ${CONDA_UID}
SHELL ["/bin/bash", "-l", "-c"]
WORKDIR /home/conda/

COPY --chown=dockeruser opera-rtc-reproject.py .

ENTRYPOINT ["python3", "-m", "opera-rtc-reproject"]
CMD ["-h"]