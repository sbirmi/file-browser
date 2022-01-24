FROM ubuntu:22.04
RUN apt update
RUN apt install -y python3 python3-flask
RUN apt install -y libimage-exiftool-perl file imagemagick ffmpeg
RUN apt install -y git

## To run latest code from github
WORKDIR /
RUN git clone https://github.com/sbirmi/file-browser.git
WORKDIR /file-browser/src
CMD ["./run.sh"]

## For development
#COPY src /src
#WORKDIR /src
#CMD ["/bin/bash"]
