. exps/prepare.sh
python -u -m coxbuild data:cleanall
cb build:$EXPS_TYPE
nohup python -u -m coxbuild -c docker=aexpy/exps -c provider=all -c project=all data:work > ./logs/all.log 2>&1 &
cb serve:$EXPS_TYPE