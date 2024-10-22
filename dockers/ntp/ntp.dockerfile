FROM archlinux:base-devel

LABEL image="dunderlab/ntp"
LABEL version="1.1"
LABEL maintainer="yencardonaal@unal.edu.co"
LABEL description=""
LABEL project=""
LABEL documentation=""
LABEL license="BSD 2-Clause"

RUN pacman --noconfirm -Suy \
    && pacman --noconfirm -S ntp

COPY ntp.conf /etc/

EXPOSE 123/udp

CMD ["ntpd", "-n", "-g"]
