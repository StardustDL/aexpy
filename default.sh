. prepare.sh
python -u -m coxbuild data:clean
cb build:exps
nohup python -u -m coxbuild -c docker=aexpy -c provider=default -c project=all data:work > ./logs/default.log 2>&1 &
cb serve:exps