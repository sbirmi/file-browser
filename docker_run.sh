## Can also use the following to store data outside of the docker container
# docker run -it -p 4090:5000 --mount type=bind,source=/path/to/persistent/data,target=/src/data file-browser
docker run -it -p 4090:5000 file-browser
