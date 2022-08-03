. exps/prepare.sh
python -u -m coxbuild data:cleanall
cb build:exps
nohup python -u -m coxbuild -c docker=aexpy -c provider=all -c project=full data:work > ./logs/full.log 2>&1 &
cb serve:exps