. prepare.sh
rm -rf ./logs/*
sudo rm -rf ../aexpy-exps/*
cb build:exps
cb serve:exps