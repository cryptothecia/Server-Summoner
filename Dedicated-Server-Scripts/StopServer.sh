#!/bin/bash
cd "$(dirname "$0")" || exit
source ./.PATHS
while getopts g: l
do
	case "${l}" in
		g) game=${OPTARG};;
		*) game=null;;
	esac
done

backupStatus=$(systemctl status "${game}Backup.service" | grep -w -A 1 "Backup.sh -g ${game}" | grep -v 'Backup.sh')
if [[ $backupStatus == *"sleep"* || -z "$backupStatus" ]]; then
	sudo systemctl stop "${game}Backup.service"
fi

serverStatus=$(systemctl is-active "${game}Server.service")
if [[ $serverStatus == "active" ]]; then
	if [[ $game == "7D2D" ]]; then
		echo say \"IT IS TIME TO STOP.\" | ncat localhost 8081 &
		sleep 2
		echo say \"The server will be shutting down in ten minutes.\" | telnet localhost 8081 &
		sleep 300
		echo say \"The server will be shutting down in five minutes.\" | telnet localhost 8081 &
		sleep 60
		echo say \"The server will be shutting down in four minutes.\" | telnet localhost 8081 &
		sleep 60
		echo say \"The server will be shutting down in three minutes.\" | telnet localhost 8081 &
		sleep 60
		echo say \"The server will be shutting down in two minutes.\" | telnet localhost 8081 &
		sleep 60
		echo say \"The server will be shutting down in one minute.\" | telnet localhost 8081 &
		sleep 60
		echo shutdown | telnet localhost 8081
	fi
	sudo systemctl stop "${game}"Server.service
	echo "" > "${currentGameFullPath}"
fi