FROM mambaorg/micromamba:1.5.8

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1

WORKDIR /opt/autoretroab
COPY --chown=$MAMBA_USER:$MAMBA_USER . /opt/autoretroab
RUN pip install --no-cache-dir .

WORKDIR /data

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "autoretroab"]
CMD ["--help"]
