. exps/prepare.sh
python -u -m coxbuild data:cleanall
cb build:$EXPS_TYPE
EXPS_PROVIDER="default"

if [ $EXPS_TYPE == "exps" ];
then  
EXPS_PROVIDER="all"
fi

nohup python -u -m coxbuild -c docker=aexpy/exps -c provider=$EXPS_PROVIDER -c project=full data:work > ./logs/full.log 2>&1 &
cb serve:$EXPS_TYPE