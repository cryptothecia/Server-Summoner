import socket
import subprocess
import glob

# Build list of games that the dedicated server can run
servicePath = '/etc/systemd/system/*Server.service'
games = glob.glob(servicePath)
i = 0
for game in games:
    games[i] = game.replace((servicePath.split("*"))[0],'').replace((servicePath.split("*"))[1],'')
    i+=1
# End game list build

host = ''
port = 62487
buffer_size = 20
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
s.listen(1)

def check_game_services(game: str,backupRequested: bool):
    serverStatus = subprocess.run(['systemctl', 'is-active', f'{game}Server.service'], text=True, stdout=subprocess.PIPE)
    if backupRequested == True:
        backupStatus = subprocess.run(['systemctl', 'is-active', f'{game}Backup.service'], text=True, stdout=subprocess.PIPE)
        return serverStatus.stdout.strip(), backupStatus.stdout.strip()
    else: 
        return serverStatus.stdout.strip()
    
def start_game_services(game: str,backupRequested: bool):
    subprocess.run(['sudo', 'systemctl', 'start', f'{game}Server.service'], text=True)
    if backupRequested == True:
        subprocess.run(['sudo', 'systemctl', 'start', f'{game}Backup.service'], text=True)

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

def reply(request):
    match request:
        case "status":
            activeGames = get_current_game()
            if activeGames == None: 
                return " running"
            else: 
                return ''.join(activeGames) + " running"
        case request if request in games:
            serverStatus, backupStatus = check_game_services(request,True)
            if serverStatus == "inactive":
                activeGames = get_current_game()
                if activeGames is None:
                    backupRequest = False
                    if backupStatus == "inactive":
                        backupRequest = True
                    start_game_services(request,backupRequest)
                    return f"Bringing {request} server online."
                else:
                    return ''.join(activeGames) + " running"
            elif serverStatus == "active":
                return f"{request} running"
            else:
                return "Error"
        case _:
            return "No request made"

conn, addr = s.accept()
while True:
    request = conn.recv(buffer_size).decode()
    if request: 
        print('received:', request)
        answer = reply(request)
        print('sent:', answer)
        conn.send(answer.encode())
    if not request: 
        conn, addr = s.accept()