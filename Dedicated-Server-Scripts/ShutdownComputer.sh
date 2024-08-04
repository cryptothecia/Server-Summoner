#! /bin/bash
### This script should be added to crontab, set to start at the time you want the dedicated server to start trying to shut down
cd "$(dirname "$0")" || exit
source ./.PATHS
OLDIFS=$IFS
IFS=',' read -r -a pingTargets <<< "$pingTargets"
IFS=$OLDIFS

while [[ $DesktopShutdown != "true" ]]; do
	### The computer running the DedicatedServerController pings the addresses in pingTargets and will only proceed with scheduled shutdown if all addresses give no ping response.
	### If no pingTargets exist, then the DedicatedServerController will proceed with cleanup and shutdown as soon as the script is started
	i=0
	for target in "${pingTargets[@]}"; do
		pingResults[i]=$(ping "${target}" -c 4)
		(("i++"))
	done
	anyOnline=$(echo "${pingResults[@]}" | wc -w)
	if [[ $anyOnline -eq 0 ]]; then
	((PingFails++))
	if [[ $PingFails -ge 2 ]]; then
		serverStatus=$(systemctl is-active -- *Server.service | grep -v "inactive") 
		if [[ ! -z $serverStatus ]]; then 
			runningServers=$(systemctl status -- *Server.service | grep -o '.system.slice.*Server.service' | sed 's/.system.slice.//' | sed 's/Server.service//')
			for game in $runningServers; do
				source ./StopServer.sh -g "${game}"
			done
		fi
		DesktopShutdown="true"
	fi
	else
		sleep $((5*60))
	fi
done
sudo systemctl stop DedicatedServerController.service
sudo /usr/sbin/shutdown -P now