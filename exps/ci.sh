nohup python exps/ci.py > ./logs/ciraw.log 2>&1 &
ps -A -f | grep python