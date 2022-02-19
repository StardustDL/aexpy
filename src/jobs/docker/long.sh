projects="urllib3 python-dateutil requests pyyaml jmespath numpy click pandas flask tornado django scrapy coxbuild"

docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/data --name pidif aexpy -p pidiff pro $projects
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/data --name pidif aexpy -p pycompat pro $projects
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/data --name pidif aexpy pro $projects

while ((2>1)); do ls ./cache/diff | wc -l; sleep 10; done

# ssh test@192.168.1.102 "while ((2>1)); do date; ls ~/liang/aexpy/src/main/cache/diff | wc -l; sleep 10; done"