#Server Summoner Bot
import os
import discord
import socket
import struct
import datetime
import time
from threading import *
from discord import app_commands
from discord.ext import tasks, commands
from dotenv import load_dotenv
from typing import Literal
from cryptography.fernet import Fernet

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DedicatedServerToken = os.getenv('DedicatedServerToken')
fernet = Fernet(DedicatedServerToken)
DedicatedServerHostname = os.getenv('DedicatedServerHostname')
logging = (os.getenv('logging')) == "True"
logFile = os.path.join((os.path.abspath(__file__)).replace(os.path.basename(__file__),""),"summonerlog.txt")
botOwner = os.getenv('BotOwnerID')
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
port = 62487
buffer = 1024
requestIsQueued = False
queuedRequest = queuedRequestTime = requestTime = None
        
games = {
    "Palworld" : {"LongName" : "Palworld", "AppID" : 0},
    "7D2D" : {"LongName" : "7 Days to Die", "AppID" : 0},
    "Enshrouded" : {"LongName" : "Enshrouded", "AppID" : 0},
    "ARKSE" : {"LongName" : r"ARK: Survival Evolved", "AppID" : 0},
    "Satisfactory" : {"LongName" : "Satisfactory", "AppID" : 0}
}

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

### Logs command usage
def log(logMessage: str):
    if logging is True:
        if (os.path.isfile(logFile)) is False:
            with open(logFile, "w") as f:
                f.write("")
        with open(logFile, "a", encoding="utf-8") as f:
            time = datetime.datetime.now()
            try: 
                f.write(time.strftime("%Y/%m/%d_%H:%M:%S") + ":: " + logMessage + "\n")
            except: 
                f.write(time.strftime("%Y/%m/%d_%H:%M:%S") + ":: " + "A log entry was attempted, but an error occurred." + "\n")

### Used as a permission check for commands, checks if user is botOwner defined in the .env
def is_owner(interaction: discord.Interaction):
    if str(interaction.user.id) == botOwner:
        return True
    return False

async def set_bot_status(status=None):
    if status is None:
        await bot.change_presence()
    else: 
        await bot.change_presence(activity=discord.Game(name=f"{status}"))

responsesFromServer = [
    "Bringing {game} server online.",
    " running",
    "Error",
    "No request made"
]
askServerReturnMessages = {
    "Starting" : responsesFromServer[0],
    "Timeout" : "The dedicated server was requested to come online {time} minutes ago, but is still not responding.",
    "Started" : "The dedicated server reports it is online running {game} at {ip}:{port}.",
    "Idle" : "The dedicated server is online but not running any games.",
    "Error" : "Oh dear, something went wrong. Sorry.",
    "Offline" : "The dedicated server is not online."
}

### This is only used in a seperate thread to wake up the Dedicated Server machine
def wake_server():
    serverOnline = False
    wakeLoops = 0
    while serverOnline is not True:
        send_wol()
        try: 
            host = socket.gethostbyname(DedicatedServerHostname)
            try:
                global requestIsQueued
                global queuedRequest
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                s.send(queuedRequest.encode())
                reply = s.recv(buffer)
                s.close()
                if reply == responsesFromServer[0].replace("game",queuedRequest):
                    set_bot_status(games[queuedRequest]["LongName"])
                requestIsQueued = False
                queuedRequest = None
                serverOnline = True
            except: 
                print("wake_server can find IP but can't send a message, sleeping.")
                time.sleep(10)
        except:
            print("wake_server cannot find IP, sleeping.")
            time.sleep(10)
        wakeLoops += 1
        if wakeLoops > 20:
            print("wake_server has run more than 20 times, stopping wake_server")
            break

class Reply:
    def __init__(self, rawReply):
        self.text = rawReply[0]
        try:
            self.ip = rawReply[1]
        except: 
            self.ip = "0"
        try: 
            self.port = rawReply[2]
        except: 
            self.port = "0"

### Sends messages to the Dedicated Server machine that is running DedicatedServerController.py and returns a string for the end user based on results
async def ask_server(request: str):
    askFailure = False
    try: 
        host = socket.gethostbyname(DedicatedServerHostname)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            encoded_message=fernet.encrypt(request.encode())
            s.send(fernet.encrypt(request.encode()))
            print(DedicatedServerToken)
            print(fernet.decrypt(encoded_message).decode())
            print(encoded_message)
            print(len(encoded_message))
            rawReply = s.recv(buffer)
            rawReply = fernet.decrypt(rawReply).decode()
            s.close()
            reply = Reply(rawReply.split("::"))
            print(reply.text)
        except: 
            print("Server has IP but not answering.")
            askFailure = True
    except: 
        print("Server does not have IP.")
        askFailure = True      
    if request in games and askFailure is True:
        global queuedRequest
        global requestIsQueued
        queuedRequest = request
        if requestIsQueued is False: 
            requestIsQueued = True
            global requestTime
            requestTime = time.time()
            thread = Thread(target=wake_server,daemon=True)
            thread.start()
            return askServerReturnMessages["Starting"].format(game = games[request]["LongName"])
        else:
            if (time.time() - requestTime) > (10*60):
                return askServerReturnMessages["Timeout"].format(time = f"{(time.time() - requestTime)/60:.0f}")
            else:
                return askServerReturnMessages["Starting"].format(game = games[request]["LongName"])
    elif askFailure is True:
        await set_bot_status()
        return askServerReturnMessages["Offline"]
    try:
        match reply.text: 
            case reply.text if reply.text == responsesFromServer[0].format(game = request):
                await set_bot_status(games[request]["LongName"])
                return askServerReturnMessages["Starting"].format(game = games[request]["LongName"].replace(".","") + f" at {reply.ip}:{reply.port}.")
            case reply.text if responsesFromServer[1] in reply.text:
                activeGames = reply.text.replace(responsesFromServer[1],"")
                if activeGames != "":
                    i=0
                    for game in games:
                        if game in activeGames:
                            replacement = True
                            activeGames = activeGames.replace(list(games.keys())[i],games[list(games.keys())[i]]["LongName"])
                            activeGames = activeGames + " and "
                        i+=1
                    if replacement == True:
                        activeGames = activeGames[:-5]
                    await set_bot_status(activeGames)
                    return askServerReturnMessages["Started"].format(game = activeGames, ip = reply.ip, port = reply.port)
                else:
                    await set_bot_status()
                    return askServerReturnMessages["Idle"]
            case _:
                return askServerReturnMessages["Error"]
    except:
        pass

@bot.event
async def on_ready():
    log("")
    log(f'{bot.user} has connected to Discord!')
    auto_status_update.start()
    await tree.sync() 

@tasks.loop(seconds=600.0)
async def auto_status_update():
    await ask_server("status")

### Mostly just a wrapper for ask_server
async def summon(summonedGame,interaction):
    await interaction.response.defer(ephemeral=True,thinking=True)
    log(f"{interaction.user.global_name} used {interaction.command.name} in {interaction.channel} in {interaction.guild}")
    message = await ask_server(summonedGame)
    await interaction.followup.send(message,ephemeral=True)
    log(f"Sent to {interaction.user.global_name}: \"" + message + "\"")
    
### LIST OF COMMANDS STARTS HERE
@tree.command(name="summonstatus",description=f"Get server status.")
async def summonstatus(interaction: discord.Interaction):
    await summon("status",interaction=interaction)
    
@tree.command(name="summongame",description=f"Send a request to bring a game server online.")
async def summongame(interaction: discord.Interaction, 
                     game: Literal[tuple(games.keys())]):
    await summon(game,interaction=interaction)

### ADMIN ONLY COMMANDS
@tree.command(name="summonlogs",description=f"ADMIN ONLY. Returns latest log entries.")
@app_commands.check(is_owner)
async def summonlogs(interaction: discord.Interaction,number_of_lines: int = 20):
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

bot.run(DISCORD_TOKEN)