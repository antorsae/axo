#!/bin/bash

usage() { echo "Usage: $0 [-p <DIR_TO_ECP_FILES>] [-w <WOOFER_EXTRA_FILTERS>] [-m <MID_EXTRA_FILTERS>] [-t <TWEETER_EXTRA_FILTERS>]" 1>&2; exit 1; }

while getopts ":p:w:m:t" o; do
    case "${o}" in
        p)
            PREFIX=${OPTARG}
            ;;
        w)
            WOOFER=${OPTARG}
            ;;
	m)
	    MID=${OPTARG}
	    ;;
	t)  TWEETER=${OPTARG}
	    ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "$PREFIX" ] ; then
    PREFIX="/home/pi/axo/orion-331-matched"
fi

set -x
ecasound -d:2 -z:nodb -b:256 -z:mixmode,sum -x -f:s32,2,44100 \
          -a:pre1 -i:stdin -pf:$PREFIX/pre1.ecp -f:f64 -o:loop,1 \
          -a:pre2,woofer -i:loop,1 \
          -a:mid,tweeter -i:loop,2 \
          -a:pre2 -pf:$PREFIX/pre2.ecp -o:loop,2 \
          -a:woofer $WOOFER -pf:$PREFIX/woofer.ecp -chorder:0,0,1,0,0,2 \
          -a:mid $MID -pf:$PREFIX/mid.ecp -chorder:0,1,0,0,2,0 \
          -a:tweeter $TWEETER -pf:$PREFIX/tweeter.ecp -chorder:1,0,0,2,0,0 \
          -a:woofer,mid,tweeter -f:24,6 -o:stdout

