. exps/prepare.sh
rm -rf ./logs/*
sudo rm -rf ../aexpy-exps/*
cb build:$EXPS_TYPE
cb serve:$EXPS_TYPE