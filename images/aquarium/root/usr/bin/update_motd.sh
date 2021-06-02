#!/bin/sh



INTERFACES=`ip addr| awk '/.*: .*: / {print $2}'`

for i in $INTERFACES; do

LINE="$LINE$i\\t`ip addr show $i | grep "inet " | awk '{gsub(/\//,"\\\/")} 1 {print $2}'`\n"

done

sed 's/<<network interfaces>>/'"$LINE"'/' /etc/motd.template > /etc/motd

exit 0
