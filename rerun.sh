name=$(date -I)
rm -rf ./logs/*
cb build:docker
python -u -m coxbuild data:cleanall
nohup python -u -m coxbuild -c docker=aexpy -c provider=all -c project=all data:work > ./logs/$name.log 2>&1 &