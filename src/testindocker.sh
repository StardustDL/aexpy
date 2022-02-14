sudo rm -rf ./cache/analysis
sudo rm -rf ./cache/diff

docker build -t aexpy .
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy-cached:/app/cache aexpy
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy-cached:/app/cache --name download aexpy download
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy-cached:/app/cache --name diff aexpy diff

while ((2>1)); do ls ./cache/diff | wc -l; sleep 10; done

# ssh test@192.168.1.102 "while ((2>1)); do date; ls ~/liang/aexpy/src/main/cache/diff | wc -l; sleep 10; done"