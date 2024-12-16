#! /bin/bash
### Set up user and group
groupadd steam-group
password=$(tr -dc 'A-Za-z0-9!?%=' < /dev/urandom | head -c 25)
useradd server -m -g steam-group
echo "server:$password" | chpasswd
unset password

## Set up directory for Steam files
mkdir /shared-steam-library
chown server:steam-group /shared-steam-library 

### Install pre-requisites for SteamCMD and install SteamCMD
sudo add-apt-repository multiverse
sudo dpkg --add-architecture i386
sudo apt install steamcmd

### Permanently maps network drive
echo "Enter network address of machine hosting network location (machine name can be used on local network)."
read -pr "" networkDriveHost
echo "Enter username, password, and domain for network location."
read -pr "Username: " username
read -spr "Password: " password; echo
read -pr "Domain: " domain
echo -e "username=$username\npassword=$password\ndomain=$domain" > /shared-steam-library/.smbcredentials
mkdir /media/Folder
echo "//$networkDriveHost/Folder /media/Folder cifs uid=server,credentials=/shared-steam-library/.smbcredentials,noperm 0 0" | sudo tee -a /etc/fstab

### Installs ncat for talking to 7d2d server
sudo apt install ncat -y
