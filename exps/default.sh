. exps/prepare.sh
python -u -m coxbuild data:clean
cb build:$EXPS_TYPE
nohup python -u -m coxbuild -c docker=aexpy/aexpy -c provider=default -c project=all data:work > ./logs/default.log 2>&1 &
cb serve:$EXPS_TYPE