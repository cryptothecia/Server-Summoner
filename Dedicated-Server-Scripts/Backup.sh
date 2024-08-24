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

log(){
    echo "$(date +%Y/%m/%d_%H:%M:%S):: $*" >> "$saveLog"
}

while :; do
    ### This block takes the game name passed to the script and uses variables defined from .PATHS that match the game name
    backupLocation=_${game}_BackupLocation
    backupLocation=${!backupLocation}
    savePath=_${game}_SaveLocation
    savePath=${!savePath}
    saveLog="${backupLocation}/${game}_save_log.txt"
    ### End block

    if [[ ! -z $backupLocation && ! -z $savePath ]]; then
        newFolderEnd=/$(date "+%m-%d-%y Hour %H")
        backupNewEntryPath="${backupLocation}${newFolderEnd}"
        existingBackups=("${backupLocation}/"*Hour*)
        lastBackup=${existingBackups[0]}
        for d in "${existingBackups[@]}"; do
            if [[ $d -nt $lastBackup ]]; then
                lastBackup=$d
            fi
        done
        if [[ $lastBackup != "$backupNewEntryPath" ]]; then
            mkdir -p "${backupNewEntryPath}" && rsync -rt "${savePath}" "${backupNewEntryPath}"
            log "Backup created at ${backupNewEntryPath}"
            newBackupDifference=$(diff -qrN "${lastBackup}" "${backupNewEntryPath}")
            if [[ -z $newBackupDifference ]]; then
                rm -r "${backupNewEntryPath}"
                log "Newly created backup ${backupNewEntryPath} was deleted because it was identical to ${lastBackup}."
            fi
        else
            log "The last backup path is the same as ${backupNewEntryPath}. This is normal if a backup happened within an hour of this attempt."
        fi
        while [[ $noDeletions -ne 1 && ${#existingBackups[@]} -gt 11 ]]; do
            existingBackups=("${backupLocation}/"*Hour*)
            oldestBackup=${existingBackups[0]}
            for d in "${existingBackups[@]}"; do
                if [[ $d -ot $oldestBackup ]]; then
                    oldestBackup=$d
                fi
            done
            oldestBackupAge=$(date -r "${oldestBackup}" +%s)
            lastBackupAge=$(date -r "${lastBackup}" +%s)
            if [[ $((lastBackupAge - oldestBackupAge)) -gt 172800 ]]; then
                oldBackupDifference=$(diff -qrN "${backupNewEntryPath}" "${oldestBackup}")
                if [[ ! -z $oldBackupDifference ]]; then
                    rm -r "${oldestBackup}"
                    log "${oldestBackup} was deleted due to age."
                else
                    noDeletions=1
                fi
            else
                noDeletions=1
            fi
        done  
    else
        echo "backupLocation or savePath was null, _${game}_BackupLocation or _${game}_SaveLocation entries in .PATHS may be missing." 
    fi
    sleep $((60*60))
done