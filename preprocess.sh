# preprocess.sh input.wav output.wav [ecp-directory]

if [ -z "$3" ]
  then
    PREFIX="./"
  else
    PREFIX="$3"
fi
ecasound -d:2 -z:mixmode,sum -x \
          -a:pre1 -i:"$1" -pf:$PREFIX/pre1.ecp -o:loop,1 \
          -a:pre2,woofer -i:loop,1 \
          -a:mid,tweeter -i:loop,2 \
          -a:pre2 -pf:$PREFIX/pre2.ecp -o:loop,2 \
          -a:woofer -pf:$PREFIX/woofer.ecp -chorder:0,0,1,0,0,0,2,0 \
          -a:mid -pf:$PREFIX/mid.ecp -chorder:0,1,0,0,0,2,0,0 \
          -a:tweeter -pf:$PREFIX/tweeter.ecp -chorder:1,0,0,0,2,0,0,0 \
          -a:woofer,mid,tweeter -f:24,8 -o:$2

