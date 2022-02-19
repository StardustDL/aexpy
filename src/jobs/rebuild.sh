set -x -e -u -o pipefail

export PYTHONUTF8=1
conda activate aexpy
docker build -t aexpy .

python -u -m aexpy rebuild
docker build -t aexpy .
docker rmi $(docker images -f "dangling=true" -q)