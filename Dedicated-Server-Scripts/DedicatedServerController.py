# Dedicated Server Controller, to be run on a Linux machine hosting the 
# dedicated server programs
import socket
import subprocess
import glob
import os
import urllib.request
import random
import string
from cryptography.fernet import Fernet
from time import sleep

servicePath = '/etc/systemd/system/*Server.service'
parentPath = (os.path.abspath(__file__)).replace(os.path.basename(__file__),"")
PATHSfile = os.path.join(parentPath,".PATHS")
external_ip = None
games = []
botHost = ''
host = ''
port = 62487
buffer_size = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
s.listen(1)

while external_ip is None:
    try: 
        external_ip = urllib.request.urlopen(
            'https://ident.me').read().decode('utf8')
    except:
        print("external_ip retrieval failed")
        sleep(30)

# Function for searching .PATHS for different variables
def read_PATHS(query):
    with open(PATHSfile,"r", encoding="utf-8") as f:
        for line in f.readlines():
            if query in line:
                result = line.replace(query,'')
                result = result.strip()
                return result
            
DedicatedServerToken = read_PATHS("DedicatedServerToken=")
fernet = Fernet(DedicatedServerToken)

# Get hostname of machine hosting SummonerBot.py from .PATHS
def get_bot_host():
    global botHost
    botHost = read_PATHS("botHost=")
    if botHost != '':
        botHost = socket.gethostbyname(botHost)

# Build list of games that the dedicated server can run
def get_games():
    global games
    games = glob.glob(servicePath)
    i = 0
    for game in games:
        games[i] = (
            game.replace((servicePath.split("*"))[0],'')
            .replace((servicePath.split("*"))[1],'')
        )
        i+=1

# Creates new Server, ServerStop and Backup .services for the requested game
def create_game_services(game:str):
    path = servicePath.replace('*',game)
    with open(os.path.join(parentPath,"TEMPLATE_Server.service"),"r") as f:
        serverService=(
            f.read()
            .replace("Game",game)
            .replace("PATH/",str(parentPath))
        )
    with open(os.path.join(parentPath,"TEMPLATE_Backup.service"),"r") as f:
        backupService=(
            f.read()
            .replace("Game",game)
            .replace("PATH/",str(parentPath))
        )
    with open(os.path.join(parentPath,"TEMPLATE_ServerStop.service"),"r") as f:
        serverStopService=(
            f.read()
            .replace("Game",game)
            .replace("PATH/",str(parentPath))
        )
    def create_service(servicePath, serviceBody):
        with open(servicePath,"w") as f:
            f.write(serviceBody)
        if (os.path.isfile(servicePath)) is True:
            subprocess.run(["sudo", "chmod", "+x", servicePath], text=True)
    create_service(path,serverService)
    create_service(path.replace("Server.service","Backup.service"),
                   backupService)
    create_service(path.replace("Server.service","ServerStop.service"),
                   serverStopService)
    get_games()
    subprocess.run(['sudo','systemctl','daemon-reload'], text=True)

# Invokes create_game_services if there are no services for the requested game,
# then checks the status of the services    
def check_game_services(game:str,backupRequested:bool):
    path = servicePath.replace('*',game)
    if (os.path.isfile(path)) is False:
        create_game_services(game)
    serverStatus = subprocess.run(['systemctl', 
                                   'is-active', 
                                   f'{game}Server.service'], 
                                   text=True, 
                                   stdout=subprocess.PIPE)
    if backupRequested == True:
        backupStatus = subprocess.run(['systemctl', 
                                       'is-active', 
                                       f'{game}Backup.service'], 
                                       text=True, 
                                       stdout=subprocess.PIPE)
        return serverStatus.stdout.strip(), backupStatus.stdout.strip()
    else: 
        return serverStatus.stdout.strip()
 
# Starts the services for the requested game 
def start_game_services(game:str,backupRequested:bool):
    subprocess.run(['sudo', 
                    'systemctl', 
                    'start', 
                    f'{game}Server.service'], 
                    text=True)
    if backupRequested == True:
        subprocess.run(['sudo', 
                        'systemctl', 
                        'start', 
                        f'{game}Backup.service'], 
                        text=True)

# Returns what game(s) has services currently running
def get_current_game():
    ag = []
    for game in games:
        serverStatus = check_game_services(game,False)
        if serverStatus == "active":
            ag.append(game)
        serverStatus = None
    if ag == []: 
        return None
    else:
        return ag

# Invokes functions in response to requests from SummonerBot.py,
# always returning a string as an answer
def reply(request):
    request=''.join(c for c in request if c.isalnum())
    match request:
        case "status":
            activeGames = get_current_game()
            if activeGames == None: 
                return " running"
            else: 
                r = ''.join(activeGames)
                if r in games:
                    rPort = read_PATHS(f"_{r}_Port=")
                    return r + f" running::{external_ip}::{rPort}"
                else:
                    return r + f" running::0"
        case "shutdown":
            subprocess.run(['sudo', 
                            'systemctl', 
                            'start', 
                            'ShutdownComputer.service', 
                            '&'], 
                            text=True)
            return "shutting down"
        case request if request != "status" and request != "shutdown":
            serverStatus, backupStatus = check_game_services(request,True)
            if serverStatus == "inactive":
                activeGames = get_current_game()
                if activeGames is None:
                    backupRequest = False
                    if backupStatus == "inactive":
                        backupRequest = True
                    start_game_services(request,backupRequest)
                    return (f"Bringing {request} server online.::"
                            f"{external_ip}::"
                            f"{read_PATHS(f"_{request}_Port=")}")
                else:
                    return ''.join(activeGames) + f" running::{external_ip}"
            elif serverStatus == "active":
                return (f"{request} running::"
                        f"{external_ip}::"
                        f"{read_PATHS(f"_{request}_Port=")}")
            else:
                return "Error"
        case _:
            return "No request made"

# Builds salt string for messages between
# SummonerBot and Dedicated Server Controller
def make_salt():
    chars = string.ascii_letters + string.punctuation + string.digits
    chars = chars.replace(':','')
    return ''.join(random.choice(chars) for x in range(20))

def encrypt_message(message):
    salt = make_salt()
    message = salt + "::" + message
    return fernet.encrypt(message.encode())

def decrypt_message(message):
    message = fernet.decrypt(message).decode()
    message = message.split("::")
    del message[0]
    return message

def main():
    get_bot_host()
    get_games()
    # Loop for socket to listen for and send responses 
    # to requests from SummonerBot.py
    conn, addr = s.accept()
    while True:
        request = conn.recv(buffer_size)
        if request: 
            request = decrypt_message(request)
            print('received: ', request, 'from: ', addr[0])
            # Checks addr IP against the IP of botHost, 
            # defined by get_bot_host(). 
            # If IP is not the same, no action should be taken 
            # and a reject message sent. 
            # This check doesn't happen if botHost ends up blank
            if botHost != '' and addr[0] == botHost:
                answer = reply(request)
            elif botHost != '' and addr[0] != botHost:
                answer = "Rejected request."
            print('sent:     ', answer)
            conn.send(encrypt_message(answer))
        if not request: 
            conn, addr = s.accept()

if __name__ == '__main__':
    main()