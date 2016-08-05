#! /bin/sh
# /etc/init.d/denon.sh

#touch /var/lock/DENON

case "$1" in
  start)
    if [ "$2" = "log" ]; then
      echo "Starting serial connection to DENON with logging... "
      /usr/bin/screen -dmS DENON /dev/ttyUSB0 9600
    else 
      echo "Starting serial connection to DENON without logging... "
      /usr/bin/screen -dmS DENON /dev/ttyUSB0 9600
    fi
  ;;
  stop)
    echo "Stopping serial connection to DENON ..."
    /usr/bin/screen -S DENON -X kill
  ;;
  restart)
     echo "Restarting serial connection to DENON ..."
    /usr/bin/screen -S DENON -X kill
    /usr/bin/screen -dmS DENON /dev/ttyUSB0 9600
  ;;
  send)
    if [ -n "$2" ]; then
      /usr/bin/screen -S DENON -X stuff "$2\r"
    else 
      echo "Usage: $0 $1 {command}"
    fi
  ;;
  cmd)
    if [ -n "$2" ]; then
      /usr/bin/screen -dmS DENON /dev/ttyUSB0 9600
      /usr/bin/screen -S DENON -X stuff "$2\r"
      /usr/bin/screen -S DENON -X kill
    else 
      echo "Usage: $0 $1 {command}"
    fi
  ;;
  *)
    echo "Usage: $0 {start (log) | stop | restart | send|cmd command}"
    exit 1
  ;;
esac
exit 0
