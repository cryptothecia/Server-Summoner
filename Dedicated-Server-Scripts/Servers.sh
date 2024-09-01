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

if [[ -f $serverLocation ]]; then
    ### Gets server directory by searching for index of last slash
    slashIndex=$(echo "$serverLocation" | grep -ob "/" | tail -n 1 | tr -d :/)
    serverFolder=${serverLocation:0:(slashIndex + 1)}
    ### Checks if steamcmd is a valid command
    steamCMDcheck=$(command -v steamcmd)
    ### Looks for a SteamCMD update script to run (main purpose of script would be to update the server)
    updateScript=$serverFolder"update_${game}.txt"
    if [[ -f "$updateScript" && -n $steamCMDcheck ]]; then
        steamcmd +runscript "$updateScript"
    ### If a script isn't found, one is created
    elif [[ ! -f "$updateScript" && -n $steamCMDcheck ]]; then
        steamappsFolder="$serverFolder"steamapps
        ### If steamapps folder is valid directory, read appmanifest file
        if [[ -d $steamappsFolder ]]; then
            appManifest="$steamappsFolder/appmanifest"
            findAppID=$(grep "appid" "$appManifest"* | tr -d "\"")
            appID="${findAppID:8:${#findAppID}}"
            if [[ -n $appID ]]; then 
                updateScriptTemplate=$(cat ./update_game_template.txt)
                updateScriptBody=${updateScriptTemplate//appid/$appID}
                updateScriptBody=${updateScriptBody//steam-library/$steamappsFolder}
                updateScriptBody=${updateScriptBody//steamapps/}
                echo "$updateScriptBody" > "$updateScript"
                steamcmd +runscript "$updateScript"
            fi
        fi
    elif [[ -z $steamCMDcheck ]]; then
        echo "SteamCMD is not installed."
    fi
    case "${game}" in
        "Palworld") 
            "$serverLocation" -useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS      echo "ran"
        ;;
        "7D2D")
            "$serverLocation" -configfile="${_7D2D_ServerConfig}"
        ;;
        "Enshrouded")
            wine64 "$serverLocation"
        ;;
        *)
            "$serverLocation"
    esac
else
    echo "Server location isn't valid."
fi