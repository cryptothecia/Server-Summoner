#! /bin/bash
cd "$(dirname "$0")" || exit
source ./.PATHS
while getopts g:v l
do
	case "${l}" in
		"g") game=${OPTARG};;
		"v") VM=true;;
        *) game=null;;
	esac
done

shopt -s expand_aliases
source ~/.bash_aliases

serverLocation=_${game}_ServerLocation
serverLocation="${!serverLocation}"
serverPort=_${game}_Port
serverPort="${!serverPort}"

if [[ -f $serverLocation ]]; then
    if [[ $VM != true ]]; then
        ### Checks if steamcmd is a valid command
        if command -v steamcmd; then
            ### Gets server directory and steamapps folder by searching for index of last slash, then tries to find appID
            slashIndex=$(echo "$serverLocation" | grep -ob "/" | tail -n 1 | tr -d :/)
            serverFolder=${serverLocation:0:(slashIndex + 1)}
            steamappsFolder="$serverFolder"steamapps
            while [[ ! -d $steamappsFolder ]]; do
                serverFolder=${serverFolder:0:(${#serverFolder}-1)}
                slashIndex=$(echo "$serverFolder" | grep -ob "/" | tail -n 1 | tr -d :/)
                serverFolder=${serverFolder:0:(slashIndex + 1)}
                steamappsFolder="$serverFolder"steamapps
            done
            appManifest="$steamappsFolder/appmanifest"
            findAppID=$(grep "appid" "$appManifest"* | tr -d "\"")
            appID="${findAppID:8:${#findAppID}}"
            ### Builds path and content of SteamCMD update script based on template
            updateScript=$serverFolder"update_${game}.txt"
            updateScriptTemplate=$(cat ./update_game_template.txt)
            updateScriptBody=${updateScriptTemplate//appid/$appID}
            updateScriptBody=${updateScriptBody//steam-library/$serverFolder}
            ### Only proceeds with creating or running script if an appID was found
            if [[ -n $appID ]]; then
                ### If a script isn't found or script doesn't match modified template, a new one is created
                if [[ ! -f "$updateScript" || $(cat "$updateScript") != "$updateScriptBody" ]]; then
                    echo "$updateScriptBody" > "$updateScript"
                    echo "Creating new update script."
                fi
                if [[ -f "$updateScript" ]]; then
                    steamcmd +runscript "$updateScript"
                    echo "Running update script."
                elif [[ ! -f "$updateScript" ]]; then
                    echo "Update script file not found after attempt at creating it."
                fi
            elif [[ -z $appID ]]; then
                echo "No appID found."
            fi
        else
            echo "SteamCMD is not installed."
        fi
    fi
    if [[ $(firewall-cmd --state) == "running" ]]; then
            firewall-cmd --add-port="$serverPort"/{tcp,udp}
            firewall-cmd --reload
    fi
    if [[ -f "./StartScripts/$game.sh" ]]; then
        "./StartScripts/$game.sh"
    else
        "$serverLocation"
    fi
else
    echo "Server location isn't valid."
fi