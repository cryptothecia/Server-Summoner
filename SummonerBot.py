#Server Summoner Bot
import os
import discord
import socket
import struct
import datetime
import time
from threading import *
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
currentGamePath = os.getenv('currentGamePath')
logging = (os.getenv('logging')) == "True"
logFile = os.path.join((os.path.abspath(__file__)).replace(os.path.basename(__file__),""),"summonerlog.txt")
botOwner = os.getenv('BotOwnerID')
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
DedicatedServerHostname = os.getenv('DedicatedServerHostname')
port = 62487
buffer = 1024
requestQueued = False
queuedRequest = None
queuedRequestTime = None
requestTime = None
games = {
    "Palworld" : "Palworld",
    "7D2D" : "7 Days to Die",
    "Enshrouded" : "Enshrouded"
}
responsesFromServer = [
    "Bringing game server online.",
    " running",
    "Error",
    "No request made"
]
askServerReturnMessages = [
    responsesFromServer[0],
    "The dedicated server was requested to come online time minutes ago, but is still not responding.",
    "The dedicated server reports it is already online running game.",
    "The dedicated server is online but not running any games.",
    "Oh dear, something went wrong. Sorry.",
    "The dedicated server is not online."
]

#This section builds information for sending magic packets
MAC = os.getenv('DedicatedServerMAC')
MACSplit = MAC.replace(MAC[2], '')
MACBytes = ''.join(['FFFFFFFFFFFF', MACSplit * 20])
MagicPacket = b''

for i in range(0, len(MACBytes), 2):
    MagicPacket = b''.join([
        MagicPacket,
        struct.pack('B', int(MACBytes[i: i + 2], 16))
    ])

def send_wol(iterations: int = 2):
    for i in range(iterations):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as netConnect:
            netConnect.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            netConnect.sendto(MagicPacket, ("255.255.255.255",7))
#End magic packet build

def log(logMessage: str):
    if logging is True:
        if (os.path.exists(logFile)) is False:
            with open(logFile, "w") as f:
                f.write("")
        with open(logFile, "a", encoding="utf-8") as f:
            time = datetime.datetime.now()
            try: 
                f.write(time.strftime("%Y/%m/%d_%H:%M:%S") + ":: " + logMessage + "\n")
            except: 
                f.write(time.strftime("%Y/%m/%d_%H:%M:%S") + ":: " + "A log entry was attempted, but an error occurred." + "\n")

def is_owner(interaction: discord.Interaction):
    if str(interaction.user.id) == botOwner:
        return True
    return False

def summon_server():
    serverOnline = False
    while serverOnline is not True:
        send_wol()
        try: 
            host = socket.gethostbyname(DedicatedServerHostname)
            try:
                global requestQueued
                global queuedRequest
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                s.send(queuedRequest.encode())
                data = s.recv(buffer)
                s.close()
                requestQueued = False
                queuedRequest = None
                serverOnline = True
            except: 
                print("Summon_server can find IP but can't send a message, sleeping.")
                time.sleep(10)
        except:
            print("Summon_server cannot find IP, sleeping.")
            time.sleep(10)

def ask_server(request: str):
    try: 
        host = socket.gethostbyname(DedicatedServerHostname)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.send(request.encode())
            reply = s.recv(buffer)
            reply = reply.decode()
            s.close()
            match reply: 
                case reply if reply == responsesFromServer[0].replace("game",request):
                    return reply
                case reply if responsesFromServer[1] in reply:
                    activeGames = reply.replace(responsesFromServer[1],"")
                    if activeGames != "":
                        i=0
                        for game in games:
                            if game in activeGames:
                                replacement = True
                                activeGames = activeGames.replace(list(games.keys())[i],games[list(games.keys())[i]])
                                activeGames = activeGames + " and "
                            i+=1
                        if replacement == True:
                            activeGames = activeGames[:-5]
                        return askServerReturnMessages[2].replace("game",activeGames)
                    else:
                        return askServerReturnMessages[3]
                case _:
                    return askServerReturnMessages[4]
        except: 
            print("Server has IP but not answering.")
            askFailure = True
    except: 
        print("Server does not have IP.")
        askFailure = True
    if request in games and askFailure is True:
        global queuedRequest
        global requestQueued
        queuedRequest = request
        if requestQueued is False: 
            requestQueued = True
            global requestTime
            requestTime = time.time()
            thread = Thread(target=summon_server,daemon=True)
            thread.start()
            return askServerReturnMessages[0].replace("game",request)
        else:
            if (time.time() - requestTime) > (10*60):
                return askServerReturnMessages[1].replace("time",f"{(time.time() - requestTime)/60:.0f}")
            else:
                return askServerReturnMessages[0].replace("game",request)
    else:
        return askServerReturnMessages[5]

@bot.event
async def on_ready():
    log("")
    log(f'{bot.user} has connected to Discord!')
    await tree.sync() 

async def summon(summonedGame,interaction):
    await interaction.response.defer(ephemeral=True,thinking=True)
    log(f"{interaction.user.global_name} used {interaction.command.name} in {interaction.channel} in {interaction.guild}")
    message = ask_server(summonedGame)
    await interaction.followup.send(message,ephemeral=True)
    log(f"Sent to {interaction.user.global_name}: \"" + message + "\"")
    
### LIST OF COMMANDS STARTS HERE
@tree.command(name="summonstatus",description=f"Get server status.")
async def summonstatus(interaction: discord.Interaction):
    await summon("status",interaction=interaction)

@tree.command(name="summonpalworld",description=f"Send a request to bring the {games[list(games.keys())[0]]} dedicated server online.")
async def summonpalworld(interaction: discord.Interaction):
    await summon(f"{list(games.keys())[0]}",interaction=interaction)

@tree.command(name="summon7days",description=f"Send a request to bring the {games[list(games.keys())[1]]} dedicated server online.")
async def summon7days(interaction: discord.Interaction):
    await summon(f"{list(games.keys())[1]}",interaction=interaction)

@tree.command(name="summonenshrouded",description=f"Send a request to bring the {games[list(games.keys())[2]]} dedicated server online.")
async def summonenshrouded(interaction: discord.Interaction):
    await summon(f"{list(games.keys())[2]}",interaction=interaction)

### ADMIN ONLY COMMANDS
@tree.command(name="summonlogs",description=f"ADMIN ONLY. Returns latest log entries.")
@app_commands.check(is_owner)
async def summonlogs(interaction: discord.Interaction,number_of_lines: int = 10):
    await interaction.response.defer(ephemeral=True,thinking=True)
    message = []
    with open(logFile, "r", encoding="utf-8") as f:
        for line in (f.readlines() [-number_of_lines:]):
            message.append(line)
    log(f"{interaction.user.global_name} used {interaction.command.name} in {interaction.channel} in {interaction.guild}")
    await interaction.followup.send(''.join(message),ephemeral=True)
@summonlogs.error
async def on_error(interaction: discord.Interaction, error):
    await interaction.response.defer(ephemeral=True,thinking=True)
    log(f"{interaction.user.global_name} tried to use {interaction.command.name} in {interaction.channel} in {interaction.guild}, but the command was denied.")
    await interaction.followup.send("You do not have permissions for this command.",ephemeral=True)

bot.run(TOKEN)