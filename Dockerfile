FROM mambaorg/micromamba:latest as ENV

FROM python:latest as BUILD
RUN pip install build
COPY . /src
RUN python -m build /src --outdir /dist

FROM python:3.12-slim

# COPY FROM https://micromamba-docker.readthedocs.io/en/latest/advanced_usage.html#adding-micromamba-to-an-existing-docker-image
ARG MAMBA_USER=mambauser MAMBA_USER_ID=57439 MAMBA_USER_GID=57439
ENV MAMBA_USER=$MAMBA_USER MAMBA_ROOT_PREFIX="/opt/conda" MAMBA_EXE="/bin/micromamba"
COPY --from=ENV "$MAMBA_EXE" "$MAMBA_EXE"
COPY --from=ENV /usr/local/bin/_activate_current_env.sh /usr/local/bin/_activate_current_env.sh
COPY --from=ENV /usr/local/bin/_dockerfile_shell.sh /usr/local/bin/_dockerfile_shell.sh
COPY --from=ENV /usr/local/bin/_entrypoint.sh /usr/local/bin/_entrypoint.sh
COPY --from=ENV /usr/local/bin/_dockerfile_initialize_user_accounts.sh /usr/local/bin/_dockerfile_initialize_user_accounts.sh
COPY --from=ENV /usr/local/bin/_dockerfile_setup_root_prefix.sh /usr/local/bin/_dockerfile_setup_root_prefix.sh
RUN /usr/local/bin/_dockerfile_initialize_user_accounts.sh && \
    /usr/local/bin/_dockerfile_setup_root_prefix.sh

ENV PYTHONUTF8=1 RUN_IN_CONTAINER=1 AEXPY_ENV_PROVIDER=micromamba MAMBA_SKIP_ACTIVATE=1
COPY --from=BUILD /dist /tmp/packages
RUN pip install --no-cache-dir --compile /tmp/packages/*.whl

USER $MAMBA_USER
WORKDIR /data
VOLUME [ "/data" ]
SHELL ["/usr/local/bin/_dockerfile_shell.sh"]
ENTRYPOINT [ "/usr/local/bin/_entrypoint.sh", "aexpy" ]