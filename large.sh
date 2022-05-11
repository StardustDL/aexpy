. prepare.sh
cb build:exps
nohup python -u -m coxbuild -c docker=aexpy -c provider=all -c project=large data:work > ./logs/large.log 2>&1 &
cb serve:exps