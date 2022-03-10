. prepare.sh
cb build:docker
nohup python -u -m coxbuild -c docker=aexpy -c provider=all -c project=large data:work > ./logs/large.log 2>&1 &
cb serve:docker