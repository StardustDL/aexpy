conda create -n aexpy python=3.10
conda activate aexpy
python -m pip install requirements.txt


conda activate aexpy
export PYTHONUTF8=1

projects=urllib3 python-dateutil requests pyyaml jmespath numpy click pandas flask tornado django scrapy coxbuild

nohup python -u -m aexpy -p default bat -s base $projects > ./temp/base.log 2>&1 &
nohup python -u -m aexpy -p default bat -s pre $projects > ./temp/pre.log 2>&1 &
nohup python -u -m aexpy -p default bat -s ana $projects > ./temp/default.log 2>&1 &
nohup python -u -m aexpy -p pidiff bat -s ana $projects > ./temp/pidiff.log 2>&1 &
nohup python -u -m aexpy -p pycompat bat -s ana $projects > ./temp/pycompat.log 2>&1 &
