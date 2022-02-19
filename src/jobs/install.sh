set -x -e -u -o pipefail

conda create -n aexpy python=3.10
conda activate aexpy
python -m pip install requirements.txt