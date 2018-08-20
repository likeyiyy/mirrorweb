FROM ubuntu:18.04

ENV TZ=Asia/Shanghai

COPY docker/build_scripts/ /build_scripts/

RUN bash /build_scripts/0_set_network_mirror.sh \
    && bash /build_scripts/1_init_system.sh

COPY Pipfile Pipfile.lock /dist/
RUN bash /build_scripts/2_install_python_requirements.sh
