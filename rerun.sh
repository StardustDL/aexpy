source ~/.bashrc
conda activate aexpy
rm -rf ./logs/*
python -u -m coxbuild data:clean
docker stop aexpy
cb build:docker
nohup python -u -m coxbuild -c docker=aexpy -c provider=all -c project=all data:work > ./logs/all.log 2>&1 &