#! /bin/bash
### This script should be added to crontab, set to start at the time you want the dedicated server to start trying to shut down
cd "$(dirname "$0")" || exit
source ./.PATHS
while getopts t o
do
	case "${o}" in
		"t") test="true";;
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

while [[ $systemBackedUp != "true" ]]; do
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
		if command -v pixz; then
			nice -n 19 tar -c --use-compress-program=pixz -f "$systemBackupLocation/DedicatedServerBackup$(date +%F).tar.xz" /etc /home /var /opt
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
sudo systemctl start ShutdownComputer.service