nohup python -u ./jobs/exps.py -p all -d all > ./temp/all.log 2>&1 &

nohup python -u ./jobs/exps.py -p pidiff -d all > ./temp/pidiff.log 2>&1 &
nohup python -u ./jobs/exps.py -p pycompat -d all > ./temp/default.log 2>&1 &
nohup python -u ./jobs/exps.py -p default -d all > ./temp/pycompat.log 2>&1 &

while ((2>1)); do ls ./cache/diff | wc -l; sleep 10; done

# ssh test@192.168.1.102 "while ((2>1)); do date; ls ~/liang/aexpy/src/main/cache/diff | wc -l; sleep 10; done"