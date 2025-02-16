#! /bin/bash
### Set up user and group
groupadd steam-group
password=$(tr -dc 'A-Za-z0-9!?%=' < /dev/urandom | head -c 25)
useradd server -m -g steam-group
echo "server:$password" | chpasswd
unset password

### Set up directory for Steam files
mkdir /var/opt/shared-steam-library
chown server:steam-group /var/opt/shared-steam-library 
chown g+s /var/opt/shared-steam-library

### Install pre-requisites for SteamCMD and install SteamCMD
add-apt-repository multiverse
dpkg --add-architecture i386
apt install steamcmd
echo steam steam/question select "I AGREE" | debconf-set-selections
echo steam steam/license note '' | debconf-set-selections

### Clones git repository
git clone https://github.com/cryptothecia/Server-Summoner /opt/Server-Summoner

### Permanently maps network drive
echo "Enter network address of machine hosting network location (machine name can be used on local network)."
read -pr "" networkDriveHost
echo "Enter username, password, and domain for network location."
read -pr "Username: " username
read -spr "Password: " password; echo
read -pr "Domain: " domain
echo -e "username=$username\npassword=$password\ndomain=$domain" > /var/opt/shared-steam-library/.smbcredentials
mkdir /mnt/Folder
echo "//$networkDriveHost/Folder /mnt/Folder cifs uid=server,credentials=/var/opt/shared-steam-library/.smbcredentials,noperm 0 0" | sudo tee -a /etc/fstab

### Installs ncat for talking to 7d2d server
apt install ncat -y
