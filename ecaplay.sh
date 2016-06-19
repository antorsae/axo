# preprocess.sh input.wav output.wav [ecp-directory]

if [ -z "$1" ]
  then
    PREFIX="/home/pi/axo/orion-331-matched"
  else
    PREFIX="$1"
fi
ecasound -d:2 -z:nodb -b:256 -z:mixmode,sum -x -f:s32,2,44100 \
          -a:pre1 -i:stdin -pf:$PREFIX/pre1.ecp -f:f64 -o:loop,1 \
          -a:pre2,woofer -i:loop,1 \
          -a:mid,tweeter -i:loop,2 \
          -a:pre2 -pf:$PREFIX/pre2.ecp -o:loop,2 \
          -a:woofer -pf:$PREFIX/woofer.ecp -chorder:0,0,1,0,0,2 \
          -a:mid -pf:$PREFIX/mid.ecp -chorder:0,1,0,0,2,0 \
          -a:tweeter -pf:$PREFIX/tweeter.ecp -chorder:1,0,0,2,0,0 \
          -a:woofer,mid,tweeter -f:24,6 -o:stdout

