#! /bin/bash
cd "$(dirname "$0")" || exit
source ./.PATHS
while getopts g: l
do
	case "${l}" in
		g) game=${OPTARG};;
		*) game=null;;
	esac
done

serverLocation=_${game}_ServerLocation
serverLocation="${!serverLocation}"
serverPort=_${game}_Port
serverPort="${!serverPort}"

backupStatus=$(systemctl status "${game}Backup.service" | grep -w -A 1 "Backup.sh -g ${game}" | grep -v 'Backup.sh')
if [[ $backupStatus == *"sleep"* || -z "$backupStatus" ]]; then
	sudo systemctl stop "${game}Backup.service"
fi

serverStatus=$(systemctl is-active "${game}Server.service")
if [[ $serverStatus == "active" ]]; then
    if [[ -f "./StopScripts/$game.sh" ]]; then
        "./StopScripts/$game.sh"
		wait
    fi
	sudo systemctl stop "${game}"Server.service
fi