#! /bin/bash
cd "$(dirname "$0")" || exit
source ./.PATHS

while :; do
	sleep 60
	currentGame=$(cat "${currentGameFullPath}")

	if [[ ! -z $currentGame ]]; then
		if [[ $currentGame != *"Locked"* ]]; then
			echo "${currentGame}Locked" > "${currentGameFullPath}"
		fi
		currentGame="${currentGame//Locked/}"
		serverStatus=$(systemctl is-active "${currentGame}Server.service")
		backupStatus=$(systemctl is-active "${currentGame}Backup.service")
		if [[ $serverStatus == "inactive" ]]; then
			sudo systemctl start "${currentGame}Server.service"
		fi
		if [[ $backupStatus == "inactive" ]]; then
			sudo systemctl start "${currentGame}Backup.service"
		fi
	fi
	sleep 60
done