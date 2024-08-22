#Server Summoner Bot
import os
import discord
import socket
import struct
import datetime
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
games = {
    "Palworld" : "Palworld",
    "7D2D" : "7 Days to Die",
    "Enshrouded" : "Enshrouded"
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

@bot.event
async def on_ready():
    log("")
    log(f'{bot.user} has connected to Discord!')
    await tree.sync() 

async def summon(summonedGame,interaction):
    await interaction.response.defer(ephemeral=True,thinking=True)
    log(f"{interaction.user.global_name} used {interaction.command.name} in {interaction.channel} in {interaction.guild}")
    if (os.path.exists(currentGamePath)) is False:
        with open(currentGamePath, "w") as f:
            f.write("")
    with open(currentGamePath, "r+") as f:
        currentGame = f.read().replace('\n',"")
        if currentGame == "":
            f.seek(0)
            f.write(summonedGame)
            f.truncate()
            currentGame = summonedGame
    if (f"{summonedGame}" in currentGame) and ("Locked" not in currentGame):
        send_wol()
        message = f"Bringing {games[summonedGame]} server online."
    elif "Locked" in currentGame:
        currentGame = currentGame.replace("Locked","")
        if currentGame is None:
            currentGame = "something"
        message = f"The information I have tells me the dedicated server should already be online running {games[currentGame]}."
    elif currentGame in games:
        message = f"The information I have tells me the dedicated server already has a request to bring {games[currentGame]} online."
    else:
        message = "Oh dear, something went wrong. Sorry."
    await interaction.followup.send(message,ephemeral=True)
    log(f"Sent to {interaction.user.global_name}: \"" + message + "\"")

### LIST OF COMMANDS STARTS HERE
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