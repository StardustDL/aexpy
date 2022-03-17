. prepare.sh
rm -rf ./logs/*
sudo rm -rf ../aexpy-exps/*
cb build:docker
cb serve:docker