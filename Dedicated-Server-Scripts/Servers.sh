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
if false; then
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
        ### Gets the index of "steamapps" in the serverFolder, if there is no steamapps folder in the path, the script will not be generated
        steamappsIndex=$(echo "$serverFolder" | grep -ob "steamapps" | tr -d ":stemap")
        steamappsFolder=${serverLocation:0:(steamappsIndex + 9)}
        ### If steamapps folder is valid directory, the for loop will read every appmanifest file to find one that has an installdir that matches the game being launched
        if [[ -d $steamappsFolder ]]; then
            for file in "$steamappsFolder"/appmanifest*; do
                findInstallDir=$(grep "installdir" "$file" | tr -d "\"")
                installDir="${findInstallDir:13:${#findInstallDir}}"
                ### If installdir is found that matches part of the path in serverLocation, then that file is searched for an appID, which is then used to create a script
                if [[ $serverFolder == *$installDir* ]]; then
                    findAppID=$(grep "appid" "$file" | tr -d "\"")
                    appID="${findAppID:8:${#findAppID}}"
                    if [[ -n $appID ]]; then 
                        updateScriptTemplate=$(cat ./update_game_template.txt)
                        updateScriptBody=${updateScriptTemplate//appid/$appID}
                        updateScriptBody=${updateScriptBody//steam-library/$steamappsFolder}
                        updateScriptBody=${updateScriptBody//steamapps/}
                        echo "$updateScriptBody" > "$updateScript"
                        steamcmd +runscript "$updateScript"
                        break
                    fi
                fi
            done
        fi
    elif [[ -z $steamCMDcheck ]]; then
        echo "SteamCMD is not installed."
    fi
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