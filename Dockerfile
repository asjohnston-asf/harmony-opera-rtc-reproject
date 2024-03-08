FROM mambaorg/micromamba:latest

WORKDIR /home/mambauser

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml

RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

COPY --chown=$MAMBA_USER:$MAMBA_USER opera-rtc-reproject.py /home/mambauser/opera-rtc-reproject.py
COPY --chown=$MAMBA_USER:$MAMBA_USER cat.jpg /home/mambauser/cat.jpg

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python", "-m", "opera-rtc-reproject"]
