FROM mambaorg/micromamba:1.5.8
USER root

COPY environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1

WORKDIR /opt/autoretroab
COPY . /opt/autoretroab
RUN pip install --no-cache-dir -e .
WORKDIR /data

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "autoretroab"]
CMD ["--help"]
