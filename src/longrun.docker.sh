sudo rm -rf .~/liang/exps/extracting
sudo rm -rf .~/liang/exps/differing
sudo rm -rf .~/liang/exps/evaluating
sudo rm -rf .~/liang/exps/reporting

docker build -t aexpy .

docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/exps aexpy aexpy --help

docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/exps --name pre batch default pre
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/exps --name aexpy-default batch default ana
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/exps --name aexpy-pidiff batch pidiff ana
docker run -d -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/exps:/exps --name aexpy-pycompat batch pycompat ana

while ((2>1)); do ls ./cache/diff | wc -l; sleep 10; done

# ssh test@192.168.1.102 "while ((2>1)); do date; ls ~/liang/aexpy/src/main/cache/diff | wc -l; sleep 10; done"