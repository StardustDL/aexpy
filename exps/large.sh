. exps/prepare.sh
cb build:$EXPS_TYPE
$EXPS_PROVIDER="default"

if [ $EXPS_TYPE == "exps" ];  
then  
$EXPS_PROVIDER="all"
fi  

nohup python -u -m coxbuild -c docker=aexpy -c provider=$EXPS_PROVIDER -c project=large data:work > ./logs/large.log 2>&1 &
cb serve:$EXPS_TYPE