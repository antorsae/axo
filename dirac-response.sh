# dirac-response.sh all 3.1
if [ -z "$2" ]
  then
    PREFIX="."
    SUFFIX=""
  else
    PREFIX="$2"
    SUFFIX="-$2"
fi
if [ "$1" == "all" ]
  then
   ECPFILES="pre1
pre2
woofer
mid
tweeter"
  else
   ECPFILES="$1"
fi
for ECPFILE in $ECPFILES
do
ecasound -d:2 -x -a:$ECPFILE -i:./impulses/dirac-mono.wav -pf:$PREFIX/$ECPFILE.ecp  -a:$ECPFILE -f:24 -o:./out/dirac-mono$SUFFIX-$ECPFILE.wav
done
