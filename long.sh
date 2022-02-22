mkdir logs

python -u -m coxbuild -c provider=pidiff -c project=all

nohup python -u -m coxbuild -c provider=pidiff -c project=all > ./logs/pidiff.log 2>&1 &
nohup python -u -m coxbuild -c provider=pycompat -c project=all > ./logs/default.log 2>&1 &
nohup python -u -m coxbuild -c provider=default -c project=all > ./logs/pycompat.log 2>&1 &

nohup python -u -m coxbuild -c provider=pidiff -c docker=aexpy -c project=all > ./logs/pidiff.log 2>&1 &
nohup python -u -m coxbuild -c provider=pycompat -c docker=aexpy -c project=all > ./logs/default.log 2>&1 &
nohup python -u -m coxbuild -c provider=default -c docker=aexpy -c project=all > ./logs/pycompat.log 2>&1 &