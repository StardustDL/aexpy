sudo rm -rf ./cache/analysis
sudo rm -rf ./cache/diff

docker build -t aexpy .
docker run -it -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy-cached:/app/cache aexpy
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy-cached:/app/cache --name download aexpy download
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy-cached:/app/cache --name diff aexpy diff