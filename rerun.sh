name=$(date -I)
rm -rf ./logs/*
cb build:docker
python -u -m coxbuild data:cleanall
nohup python -u -m coxbuild -c docker=aexpy -c provider=all -c project=all data:work > ./logs/$name.log 2>&1 &
nohup python -u -m coxbuild -c docker=aexpy -c provider=default -c project=all data:work > ./logs/default.log 2>&1 &