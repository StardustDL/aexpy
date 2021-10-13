docker build -t aexpy .
docker run -it -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy-cached:/app/cache aexpy