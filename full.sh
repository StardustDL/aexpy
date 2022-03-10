. prepare.sh
rm -rf ./logs/*
sudo rm -rf ../aexpy-exps/*
python -u -m coxbuild data:cleanall
cb build:docker
nohup python -u -m coxbuild -c docker=aexpy -c provider=all -c project=full data:work > ./logs/full.log 2>&1 &
cb serve:docker