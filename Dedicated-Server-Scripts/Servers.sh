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

case "${game}" in
    "Palworld") 
        "${!serverLocation}" -useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS      echo "ran"
    ;;
    "7D2D")
        "${!serverLocation}" -configfile="${_7D2D_ServerConfig}"
    ;;
    *)
        "${!serverLocation}"
esac