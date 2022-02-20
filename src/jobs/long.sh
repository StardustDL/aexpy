python -u ./jobs/exps.py -p pidiff all

nohup python -u ./jobs/exps.py -p pidiff all > ./temp/pidiff.log 2>&1 &
nohup python -u ./jobs/exps.py -p pycompat all > ./temp/default.log 2>&1 &
nohup python -u ./jobs/exps.py -p default all > ./temp/pycompat.log 2>&1 &
