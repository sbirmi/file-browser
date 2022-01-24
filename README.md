# file-browser
Web based file storage server

A tool to host your photos, videos, and files on a server. Web-based interface allows uploading and accessing files from any device.

Metadata for each uploaded file is stored in a sqlite db.

## Dependencies
1. python3
2. flask
3. exiftool - to extract exif information
4. du - to get disk usage
5. file - to get mime-type
6. diff - to compare files (check for duplicates)
7. convert - to generate thumbnails (resize, overlay text)
8. ffprobe - to get video duration
9. ffmpeg - to generate thumbnail from a video

## Installation

```
$ git clone https://github.com/sbirmi/file-browser.git
$ virtualenv -p py3 file-browser
$ cd virtualenv/src
$ source ../bin/activate
$ pip install flask
$ ./run.sh
```

Connect to http://127.0.0.1:5000!

## Running the web interface

```
$ cd src/
$ ./run.sh
```

## Backend tool to regenerate thumbnails, check for duplicates etc

```
$ cd src/
$ ./UpdateScript.py --help
2022-01-23 09:49:49 ('create table Metadata (fname text, hash_sha256 text, time_db_added timestamp, time_db_updated timestamp, deleted integer, desc text, exif text, mime_type text, exif_img_create_date timestamp, thumbnail text)',)
2022-01-23 09:49:49 commit
usage: UpdateScript.py [-h] [-d] [-t] [paths ...]

positional arguments:
  paths

optional arguments:
  -h, --help            show this help message and exit
  -d, --duplicate-check
  -t, --update-thumbnails
$
```
