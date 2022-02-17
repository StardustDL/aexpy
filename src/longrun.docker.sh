sudo rm -rf .~/liang/exps/extracting
sudo rm -rf .~/liang/exps/differing
sudo rm -rf .~/liang/exps/evaluating
sudo rm -rf .~/liang/exps/reporting

docker build -t aexpy .

docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/data aexpy --help

projects="urllib3 python-dateutil requests pyyaml jmespath numpy click pandas flask tornado django scrapy coxbuild"

docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/data --name pre aexpy bat -s pre $projects
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/data --name defau aexpy -p default bat -s ana $projects
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/data --name pidif aexpy -p pidiff bat -s ana $projects
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/data --name pycom aexpy -p pycompat bat -s ana $projects

while ((2>1)); do ls ./cache/diff | wc -l; sleep 10; done

# ssh test@192.168.1.102 "while ((2>1)); do date; ls ~/liang/aexpy/src/main/cache/diff | wc -l; sleep 10; done"