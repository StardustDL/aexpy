conda create -n aexpy python=3.10
conda activate aexpy
python -m pip install requirements.txt

source ~/.bashrc
conda activate aexpy
export PYTHONUTF8=1

projects="urllib3 python-dateutil requests pyyaml jmespath numpy click pandas flask tornado django scrapy coxbuild"

python -u -m aexpy -c ../exps -p default bat -s clr
python -u -m aexpy -c ../exps -p default bat -s bas

python -u -m aexpy pro

python -u -m aexpy pro urllib3
python -u -m aexpy pro python-dateutil
python -u -m aexpy pro requests
python -u -m aexpy pro pyyaml
python -u -m aexpy pro jmespath
python -u -m aexpy pro numpy
python -u -m aexpy pro click
python -u -m aexpy pro pandas
python -u -m aexpy pro flask
python -u -m aexpy pro tornado
python -u -m aexpy pro django
python -u -m aexpy pro scrapy
python -u -m aexpy pro coxbuild

nohup python -u -m aexpy -c ../exps -p default pro $projects > ./temp/pre.log 2>&1 &
nohup python -u -m aexpy -c ../exps -p default pro $projects > ./temp/default.log 2>&1 &
nohup python -u -m aexpy -c ../exps -p pidiff pro $projects > ./temp/pidiff.log 2>&1 &
nohup python -u -m aexpy -c ../exps -p pycompat pro $projects > ./temp/pycompat.log 2>&1 &
