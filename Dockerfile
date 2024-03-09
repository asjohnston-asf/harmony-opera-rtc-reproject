FROM mambaorg/micromamba:latest

# For opencontainers label definitions, see:
#    https://github.com/opencontainers/image-spec/blob/master/annotations.md
LABEL org.opencontainers.image.title="Harmony OPERA RTC Reproject"
LABEL org.opencontainers.image.description="Reproject OPERA RTC"
LABEL org.opencontainers.image.vendor="Alaska Satellite Facility"
LABEL org.opencontainers.image.authors="tools-bot <UAF-asf-apd@alaska.edu>"
LABEL org.opencontainers.image.licenses="BSD-3-Clause"
LABEL org.opencontainers.image.url="https://github.com/ASFHyP3/harmony-opera-rtc-reproject"
LABEL org.opencontainers.image.source="https://github.com/ASFHyP3/harmony-opera-rtc-reproject"
LABEL org.opencontainers.image.documentation="https://harmony.earthdata.nasa.gov/"

WORKDIR /home/mambauser

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml

RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

COPY --chown=$MAMBA_USER:$MAMBA_USER opera-rtc-reproject.py /home/mambauser/opera-rtc-reproject.py
COPY --chown=$MAMBA_USER:$MAMBA_USER cat.jpg /home/mambauser/cat.jpg

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python", "-m", "opera-rtc-reproject"]
