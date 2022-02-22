mkdir logs

python -u -m coxbuild -c provider=pidiff -c project=all data:work

nohup python -u -m coxbuild -c provider=pidiff -c project=all data:work > ./logs/pidiff.log 2>&1 &
nohup python -u -m coxbuild -c provider=pycompat -c project=all data:work > ./logs/pycompat.log 2>&1 &
nohup python -u -m coxbuild -c provider=default -c project=all data:work > ./logs/default.log 2>&1 &

nohup python -u -m coxbuild -c provider=pidiff -c docker=aexpy -c project=all data:work > ./logs/pidiff.log 2>&1 &
nohup python -u -m coxbuild -c provider=default -c docker=aexpy -c project=all data:work > ./logs/pycompat.log 2>&1 &
nohup python -u -m coxbuild -c provider=default -c docker=aexpy -c project=all data:work > ./logs/default.log 2>&1 &