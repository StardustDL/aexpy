. prepare.sh
python -u -m coxbuild data:cleanall
cb build:docker
nohup python -u -m coxbuild -c docker=aexpy -c provider=all -c project=ground data:work > ./logs/ground.log 2>&1 &
cb serve:docker