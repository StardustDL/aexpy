name=$(date -I)
rm -rf ./logs/*
docker stop aexpy
cb build:docker
python -u -m coxbuild data:clean
nohup python -u -m coxbuild -c docker=aexpy -c provider=default -c project=all data:work > ./logs/$name.log 2>&1 &