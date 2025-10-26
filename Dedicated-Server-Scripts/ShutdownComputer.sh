#! /bin/bash
### This script should be added to crontab, set to start at the time you want the dedicated server to start trying to shut down. It can also be run as ShutdownComputer.service with -n option to initiate a server shutdown that closes all open games first
cd "$(dirname "$0")" || exit
source ./.PATHS
while getopts tn o
do
	case "${o}" in
		"t") test="true";;
		"n") skipPings="true";;
        *);;
	esac
done

OLDIFS=$IFS
IFS=',' read -r -a pingTargets <<< "$pingTargets"
IFS=$OLDIFS

while [[ $DesktopShutdown != "true" && $test != "true" ]]; do
	### The computer running the DedicatedServerController pings the addresses in pingTargets and will only proceed with scheduled shutdown if all addresses give no ping response.
	### If no pingTargets exist, then the DedicatedServerController will proceed with cleanup and shutdown as soon as the script is started
	i=0
	for target in "${pingTargets[@]}"; do
		pingResults[i]=$(ping "${target}" -c 4)
		((i++))
	done
	anyOnline=$(echo "${pingResults[@]}" | wc -w)
	if [[ $anyOnline -eq 0 ]]; then	((PingFails++)); fi
	if [[ $PingFails -ge 2 || $skipPings == "true" ]]; then
		serverStatus=$(systemctl is-active -- *Server.service | grep -v "inactive") 
		if [[ ! -z $serverStatus ]]; then 
			runningServers=$(systemctl status -- *Server.service | grep -o '.system.slice.*Server.service' | sed 's/.system.slice.//' | sed 's/Server.service//')
			for game in $runningServers; do
				./StopServer.sh -g "${game}"
			done
		fi
		DesktopShutdown="true"
	fi
	if [[ $DesktopShutdown != "true" ]]; then sleep $((5*60)); fi
done

while [[ $systemBackedUp != "true" && $skipPings != "true" ]]; do
	if [[ ! -e $systemBackupLocation ]]; then
		mkdir "$systemBackupLocation"
	fi
	if [[ ! -z $(find "$systemBackupLocation" -name "*.tar.xz") ]]; then
		i=0
		for backup in "$systemBackupLocation"/DedicatedServerBackup*.tar.xz; do
			if [ $i == 0 ]; then
				newestBackup=$backup
			elif [[ $backup -nt $newestBackup ]]; then
				newestBackup=$backup
			fi
			i=$((i + 1))
		done
		if [[ $(($(date +%s) - $(date -r "$newestBackup" +%s))) -gt $((60 * 60 * 24 * 7)) ]]; then
			doBackup="true"
		fi
	else
		doBackup="true"
	fi
	if [[ $doBackup == "true" ]]; then
		compress=$(command -v pixz || command -v pxz)
		if [[ $compress != "" ]]; then
			compress=${compress/${compress%%"p"*}/}
			nice -n 19 tar -c --use-compress-program="$compress" -f "$systemBackupLocation/DedicatedServerBackup$(date +%F).tar.xz" /etc /home /var /opt
		else
			nice -n 19 tar -cJf "$systemBackupLocation/DedicatedServerBackup$(date +%F).tar.xz" /etc /home /var /opt
		fi
		while [[ $deleted != "true" ]]; do
			i=0
			for backup in "$systemBackupLocation"/DedicatedServerBackup*.tar.xz; do
				if [ $i == 0 ]; then
					oldestBackup=$backup
				elif [[ $backup -ot $oldestBackup ]]; then
					oldestBackup=$backup
				fi
				i=$((i + 1))
			done
			if [[ $i -gt 4 ]]; then
				rm -f "$oldestBackup"
			else
				deleted="true"
			fi
		done
	fi
	systemBackedUp="true"
done

sudo systemctl stop DedicatedServerController.service
sudo shutdown -h now