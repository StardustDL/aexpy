conda create -n aexpy python=3.10

conda activate aexpy

python -m pip install requirements.txt

export PYTHONUTF8=1


nohup python -u -m batch default base > ./temp/base.log 2>&1 &
nohup python -u -m batch default pre > ./temp/pre.log 2>&1 &
nohup python -u -m batch default ana > ./temp/default.log 2>&1 &
nohup python -u -m batch pidiff ana > ./temp/pidiff.log 2>&1 &
nohup python -u -m batch pycompat ana > ./temp/pycompat.log 2>&1 &


docker build -t aexpy .
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy-cached:/app/cache aexpy
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy-cached:/app/cache --name download aexpy download
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy-cached:/app/cache --name diff aexpy diff

while ((2>1)); do ls ./cache/diff | wc -l; sleep 10; done

# ssh test@192.168.1.102 "while ((2>1)); do date; ls ~/liang/aexpy/src/main/cache/diff | wc -l; sleep 10; done"