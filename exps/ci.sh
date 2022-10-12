nohup python exps/ci/ci.py > ./logs/ciraw.log 2>&1 &
ps -A -f | grep python