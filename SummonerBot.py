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
time = datetime.datetime.now()
logFile=os.path.join((os.path.abspath(__file__)).replace(os.path.basename(__file__),""),"summonerlog.txt")
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
games = {
    "Palworld" : "Palworld",
    "7D2D" : "7 Days to Die",
    "something" : "something"
}

#This section builds information for sending magic packets
MAC = os.getenv('MAC')
MACSplit = MAC.replace(MAC[2], '')
MACBytes = ''.join(['FFFFFFFFFFFF', MACSplit * 20])
MagicPacket = b''

for i in range(0, len(MACBytes), 2):
    MagicPacket = b''.join([
        MagicPacket,
        struct.pack('B', int(MACBytes[i: i + 2], 16))
    ])
#End magic packet build

def log(logMessage):
    if logging is True:
        if (os.path.exists(logFile)) is False:
            with open(logFile, "w") as f:
                f.write("")
        with open(logFile, "a") as f:
            f.write(time.strftime("%Y/%m/%d_%H:%M:%S") + ":: " + logMessage + "\n")

@bot.event
async def on_ready():
    log("")
    log(f'{bot.user} has connected to Discord!')
    await tree.sync() 

async def summon(summonedGame,interaction):
    await interaction.response.defer(ephemeral=True,thinking=True)
    log(f"{interaction.user.global_name} used {interaction.command.name} in {interaction.channel}")
    if (os.path.exists(currentGamePath)) is False:
        with open(currentGamePath, "w") as f:
            f.write("")
    with open(currentGamePath, "r+") as f:
        currentGame = f.read()
        if currentGame == "":
            f.seek(0)
            f.write(summonedGame)
            f.truncate()
            currentGame = summonedGame
    if (f"{summonedGame}" in currentGame) and ("Locked" not in currentGame):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as netConnect:
            netConnect.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            netConnect.sendto(MagicPacket, ("255.255.255.255",7))
        message = f"Bringing {games[summonedGame]} server online."
    elif "Locked" in currentGame:
        currentGame = currentGame.replace("Locked","").replace('\n',"")
        if currentGame is None:
            currentGame = "something"
        message = f"Looks like the dedicated server should already be online running {games[currentGame]}."
    else:
        message = "Oh dear, something went wrong. Sorry."
    await interaction.followup.send(message,ephemeral=True)
    log(f"Sent to {interaction.user}: \"" + message + "\"")

@tree.command(name="summonpalworld",description=f"Send a request to bring the {games[list(games.keys())[0]]} dedicated server online.")
async def summonpalworld(interaction: discord.Interaction):
    await summon(f"{list(games.keys())[0]}",interaction=interaction)

@tree.command(name="summon7days",description=f"Send a request to bring the {games[list(games.keys())[1]]} dedicated server online.")
async def summon7days(interaction: discord.Interaction):
    await summon(f"{list(games.keys())[1]}",interaction=interaction)

bot.run(TOKEN)