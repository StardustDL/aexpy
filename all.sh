. prepare.sh
rm -rf ./logs/*
sudo rm -rf ../aexpy-exps/*
python -u -m coxbuild data:cleanall
cb build:docker
nohup python -u -m coxbuild -c docker=aexpy -c provider=all -c project=all data:work > ./logs/all.log 2>&1 &
cb serve:docker