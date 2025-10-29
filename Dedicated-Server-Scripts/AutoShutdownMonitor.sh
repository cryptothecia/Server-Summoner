#! /bin/bash
### This script monitors CPU idle time and traffic on game ports and shuts down computer based on results. Meant for a .service file

cd "$(dirname "$0")" || exit
shopt -s lastpipe
declare -i inactive_timer

while : ; do
    
    ### Gets at each game's port in .PATHS, gets the socket if is listening, then returns nothing if there are no sending or receiving packets
    ### If nothing is returned, then inactive_timer will increase
    grep -i "port=" .PATHS | while IFS= read -r line 
    do 
        active_sockets=$(ss -lntu | tr -s ' ' | grep "0.0.0.0:${line//*Port=/}" | cut -d " " -f 3,4 | grep -v "0 0")
        if [[ $active_sockets == "" ]]; then
            inactive_timer=$inactive_timer+1
        else
            inactive_timer=0
        fi
    done

    ### Gets most recent CPU idle time percentage from sar and resets inactive_timer to 0 if idleness is below threshold
    if (( $(echo "$(sar | tail -2 | head -1 | tr -s ' ' | cut -d ' ' -f 9) < 95" | bc -l) )); then
    echo "yes"
    fi

    if [[ $inactive_timer -ge 60 ]]; then
        ./ShutdownComputer.sh -n
    fi
    sleep 60
done

