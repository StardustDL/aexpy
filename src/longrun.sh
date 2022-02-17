conda create -n aexpy python=3.10
conda activate aexpy
python -m pip install requirements.txt

source ~/.bashrc
conda activate aexpy
export PYTHONUTF8=1

projects="urllib3 python-dateutil requests pyyaml jmespath numpy click pandas flask tornado django scrapy coxbuild"

python -u -m aexpy -c ../exps -p default bat -s clr
python -u -m aexpy -c ../exps -p default bat -s bas

nohup python -u -m aexpy -c ../exps -p default bat -s pre $projects > ./temp/pre.log 2>&1 &
nohup python -u -m aexpy -c ../exps -p default bat -s ana $projects > ./temp/default.log 2>&1 &
nohup python -u -m aexpy -c ../exps -p pidiff bat -s ana $projects > ./temp/pidiff.log 2>&1 &
nohup python -u -m aexpy -c ../exps -p pycompat bat -s ana $projects > ./temp/pycompat.log 2>&1 &
