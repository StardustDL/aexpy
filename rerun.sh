git pull
source ~/.bashrc
rm -rf ./logs/*
conda activate aexpy
pkill python
docker stop aexpy-data-pro
python -u -m coxbuild data:cleanall
docker stop aexpy
cb build:docker
nohup python -u -m coxbuild -c docker=aexpy -c provider=all -c project=all data:work > ./logs/all.log 2>&1 &
cb serve:docker