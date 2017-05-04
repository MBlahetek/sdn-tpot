FROM ubuntu:14.04
MAINTAINER Matthias Blahetek "matthias.blahetek@unibw.de"
RUN mkdir /floodlight
WORKDIR /floodlight
RUN apt-get -y update && \
    apt-get -y install build-essential openjdk-7-jdk ant maven python-dev eclipse git && \
    git clone -b v1.2 git://github.com/floodlight/floodlight.git /floodlight && \
    git submodule init && \
    git submodule update && \
    ant && \
    mkdir /var/lib/floodlight && \
    chmod 777 /var/lib/floodlight && \
    rm /floodlight/src/main/resources/floodlightdefault.properties
COPY floodlightdefault.properties /floodlight/src/main/resources/
RUN apt-get -y remove ant maven git eclipse  && \
    rm -rf /var/cache/apt/*

EXPOSE 9090 6653

CMD java -jar target/floodlight.jar