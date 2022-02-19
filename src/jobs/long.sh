projects="urllib3 python-dateutil requests pyyaml jmespath numpy click pandas flask tornado django scrapy coxbuild"

for project in $projects; do
    echo "Process $project"
    python -u -m aexpy -p default pro $project > ./temp/default/$project.log 2>&1
done

python -u -m aexpy pro coxbuild

nohup python -u -m aexpy -c ../exps -p pidiff pro $projects > ./temp/pidiff.log 2>&1 &
nohup python -u -m aexpy -c ../exps -p default pro $projects > ./temp/default.log 2>&1 &
nohup python -u -m aexpy -c ../exps -p pycompat pro $projects > ./temp/pycompat.log 2>&1 &
