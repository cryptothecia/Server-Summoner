#!/bin/bash
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
	case "${game}" in
		"7D2D")
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
		;;
		*);;
	esac
	sudo systemctl stop "${game}"Server.service
fi