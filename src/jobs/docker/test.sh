set -x -e -u -o pipefail

docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy/exps:/data aexpy --help
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock aexpy -p pidiff rep more-executors@1.15.0:1.16.0
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock aexpy -p pycompat rep more-executors@1.15.0:1.16.0
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock aexpy rep more-executors@1.15.0:1.16.0

docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock -v ~/liang/aexpy/exps:/data aexpy -p pidiff batch schemdule
