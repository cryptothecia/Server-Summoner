# Server Summoner Discord Bot, to be run on a machine with more uptime than 
# Dedicated Server Controller, so that it can listen to and respond to 
# Discord messages, and then wake the Dedicated Server machine as needed
import os
import discord
import socket
import struct
import datetime
import time
import random
import string
from threading import *
from discord import app_commands
from discord.ext import tasks, commands
from dotenv import load_dotenv
from typing import Literal
from cryptography.fernet import Fernet
from json import load as load_json

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DEDICATED_SERVER_TOKEN = os.getenv('DEDICATED_SERVER_TOKEN')
DEDICATED_SERVER_HOSTNAME = os.getenv('DEDICATED_SERVER_HOSTNAME')
fernet = Fernet(DEDICATED_SERVER_TOKEN)
LOGGING = (os.getenv('LOGGING')) == "True"
LOGFILE = os.path.join(
    (os.path.abspath(__file__)).replace(os.path.basename(__file__),""),
    "summonerlog.txt"
    )
bot_owner = os.getenv('BotOwnerID')
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
port = 62487
buffer = 1024
req_is_queued = False
queued_request = q_request_time = request_time = None

p_path = (os.path.abspath(__file__)).replace(os.path.basename(__file__),"")
f_path = os.path.join(p_path, "GameList.json")
with open(f_path, 'r') as file:
    games = load_json(file)

# This section builds information for sending magic packets
MAC = os.getenv('DedicatedServerMAC')
MAC_split = MAC.replace(MAC[2], '')
MAC_bytes = ''.join(['FFFFFFFFFFFF', MAC_split * 20])
WOL_packet = b''

for i in range(0, len(MAC_bytes), 2):
    WOL_packet = b''.join([
        WOL_packet,
        struct.pack('B', int(MAC_bytes[i: i + 2], 16))
    ])

def send_wol(iterations:int = 2):
    for i in range(iterations):
        with socket.socket(
                            socket.AF_INET, 
                            socket.SOCK_DGRAM, 
                            socket.IPPROTO_UDP
                        ) as net_connect:
            net_connect.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            net_connect.sendto(WOL_packet, ("255.255.255.255",7))
# End magic packet build

# Logs command usage
def log(log_message: str):
    if LOGGING is True:
        if (os.path.isfile(LOGFILE)) is False:
            with open(LOGFILE, "w") as f:
                f.write("")
        with open(LOGFILE, "a", encoding="utf-8") as f:
            time = datetime.datetime.now()
            try: 
                f.write(time.strftime("%Y/%m/%d_%H:%M:%S") 
                        + ":: " 
                        + log_message 
                        + "\n")
            except: 
                f.write(time.strftime("%Y/%m/%d_%H:%M:%S") 
                        + ":: " 
                        + "A log entry was attempted, but an error occurred." 
                        + "\n")

def log_interaction(interaction: discord.Interaction, option=""):
    if option != "":
        option = " " + option
    log(f"{interaction.user.global_name} used "
        f"/{interaction.command.name}{option} in "
        f"{interaction.channel} in "
        f"{interaction.guild}")

def log_deny(interaction: discord.Interaction):
    log(f"{interaction.user.global_name} tried to use "
        f"{interaction.command.name} in "
        f"{interaction.channel} in "
        f"{interaction.guild}, but the command was denied.")

# Used as a permission check for commands, checks if user is bot_owner defined 
# in th .env
def is_owner(interaction: discord.Interaction):
    if str(interaction.user.id) == bot_owner:
        return True
    return False

async def set_bot_status(status = None):
    if status is None:
        await bot.change_presence()
    else: 
        await bot.change_presence(activity=discord.Game(name=f"{status}"))

resp_fr_server = [
    "Bringing {game} server online.",
    " running",
    "Error",
    "No request made",
    "shutting down"
]
ask_messages = {
    "Starting" : resp_fr_server[0],
    "Timeout" : "The dedicated server was requested to come online "
        "{time} minutes ago, but is still not responding.",
    "Started" : "The dedicated server reports it is online running "
        "{game} at {ip}:{port}.",
    "Idle" : "The dedicated server is online but not running any games.",
    "Error" : "Oh dear, something went wrong. Sorry.",
    "Offline" : "The dedicated server is not online.",
    "Shutdown" : "The dedicated server machine is shutting down."
}

# Builds salt string for messages between SummonerBot and Dedicated Server 
# Controller
def make_salt():
    chars = string.ascii_letters + string.punctuation + string.digits
    chars = chars.replace(':','')
    return ''.join(random.choice(chars) for x in range(20))

# Functions for encrypting & encoding and decrypting & decoding strings
def encrypt_message(message):
    salt = make_salt()
    message = salt + "::" + message
    return fernet.encrypt(message.encode())

def decrypt_message(message):
    message = fernet.decrypt(message).decode()
    message = message.split("::")
    del message[0]
    return message

# decrypt_message() takes reply from the server and split it into a list, 
# this turns that list into a Reply object
class Reply:
    def __init__(self, raw_reply):
        if not isinstance(raw_reply, list):
            raw_reply = [raw_reply]
        if isinstance(raw_reply[0], str):
            self.text = raw_reply[0]
        else: 
            self.text = ""
        try:
            self.ip = raw_reply[1]
        except: 
            self.ip = "0"
        try: 
            self.port = raw_reply[2]
        except: 
            self.port = "0"

# Function for sending a message to the Dedicated Server Controller machine and
# receiving a reply, includes the encryption/decryption functions
def send_message(message, host):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send(encrypt_message(message))
    print('sent:     ', message)
    raw_reply = s.recv(buffer)
    s.close()
    reply = decrypt_message(raw_reply)
    print('received: ', reply)
    reply = Reply(reply)
    return reply

# This is only used in a seperate thread to wake up the 
# Dedicated Server machine
def wake_server():
    server_online = False
    wake_loops = 0
    while server_online is not True:
        send_wol()
        try: 
            host = socket.gethostbyname(DEDICATED_SERVER_HOSTNAME)
            try:
                global req_is_queued
                global queued_request
                reply = send_message(queued_request, host)
                if reply == resp_fr_server[0].format(game=queued_request):
                    set_bot_status(games[queued_request]["LongName"])
                req_is_queued = False
                queued_request = None
                server_online = True
            except: 
                print("wake_server can find IP "
                      "but can't send a message, sleeping.")
                time.sleep(10)
        except:
            print("wake_server cannot find IP, sleeping.")
            time.sleep(10)
        wake_loops += 1
        if wake_loops > 20:
            print("wake_server has run more than 20 times,"
                  " stopping wake_server")
            break

# Sends messages to the Dedicated Server machine that is running 
# DedicatedServerController.py and returns a string for the end user based on 
# results
async def ask_server(request: str):
    ask_failure = False
    try: 
        host = socket.gethostbyname(DEDICATED_SERVER_HOSTNAME)
        try:
            reply = send_message(request, host)
        except Exception as e: 
            print("Server has IP, but there was an error:\n" + f"{e}")
            ask_failure = True
    except Exception as e:
        print("Server IP was not found.\n" + f"{e}")
        ask_failure = True      
    if request in games and ask_failure is True:
        global queued_request
        global req_is_queued
        queued_request = request
        if req_is_queued is False: 
            req_is_queued = True
            global request_time
            request_time = time.time()
            thread = Thread(target=wake_server, daemon=True)
            thread.start()
            return (ask_messages["Starting"]
                    .format(game = games[request]["LongName"]))
        else:
            if (time.time() - request_time) > (10*60):
                return (
                        ask_messages["Timeout"]
                        .format(time = f"{(time.time() 
                                           - request_time)/60:.0f}")
                        )
            else:
                return (ask_messages["Starting"]
                        .format(game = games[request]["LongName"]))
    elif ask_failure is True:
        await set_bot_status()
        return ask_messages["Offline"]
    try:
        match reply.text: 
            case reply.text if reply.text == (resp_fr_server[0]
                                              .format(game=request)):
                await set_bot_status(games[request]["LongName"])
                return (ask_messages["Starting"]
                        .format(game=games[request]["LongName"])
                        .replace(".","") 
                        + f" at {reply.ip}:{reply.port}.")
            case reply.text if resp_fr_server[1] in reply.text:
                active_games = reply.text.replace(resp_fr_server[1],"")
                if active_games != "":
                    i=0
                    for game in games:
                        if game in active_games:
                            replacement = True
                            active_games = active_games.replace(
                                list(games.keys())[i],
                                games[list(games.keys())[i]]["LongName"]
                                )
                            active_games = active_games + " and "
                        i+=1
                    if replacement == True:
                        active_games = active_games[:-5]
                    await set_bot_status(active_games)
                    return ask_messages["Started"].format(game=active_games, 
                                                         ip=reply.ip, 
                                                         port=reply.port)
                else:
                    await set_bot_status()
                    return ask_messages["Idle"]
            case reply.text if resp_fr_server[4] in reply.text:
                return ask_messages["Shutdown"]
            case _:
                return ask_messages["Error"]
    except Exception as e:
        print(e)

@bot.event
async def on_ready():
    log("")
    log(f'{bot.user} has connected to Discord!')
    auto_status_update.start()
    await tree.sync() 

@tasks.loop(seconds=1200.0)
async def auto_status_update():
    await ask_server("status")

# Mostly just a wrapper for ask_server
async def summon(summoned_game, interaction, ephemeral_choice = True):
    await interaction.response.defer(ephemeral=ephemeral_choice,thinking=True)
    message_to_user = await ask_server(summoned_game)
    await interaction.followup.send(message_to_user,ephemeral=ephemeral_choice)
    if ephemeral_choice is True:
        log(f"Sent to {interaction.user.global_name}: \"" 
            + message_to_user 
            + "\"")
    else: 
        log(f"Sent to {interaction.channel}: \"" + message_to_user + "\"")
    
# LIST OF COMMANDS STARTS HERE
@tree.command(name="summonstatus",
              description=f"Get server status.")
async def summonstatus(interaction: discord.Interaction, 
                       public_answer: Literal[("No","Yes")]): # type: ignore
    if public_answer == "No":
        ephemeral_choice = True
    else:
        ephemeral_choice = False
    log_interaction(interaction,public_answer)
    await summon("status",
                 interaction=interaction,
                 ephemeral_choice=ephemeral_choice)
    
@tree.command(name="summongame",
              description=f"Send a request to bring a game server online.")
async def summongame(interaction: discord.Interaction, 
                     game: Literal[tuple(games.keys())]): # type: ignore
    log_interaction(interaction,option=game)
    await summon(game,interaction=interaction)

# ADMIN ONLY COMMANDS
@tree.command(name="summonlogs",
              description=f"ADMIN ONLY. Returns latest log entries.")
@app_commands.check(is_owner)
async def summonlogs(interaction: discord.Interaction, 
                     number_of_lines: int = 20):
    await interaction.response.defer(ephemeral=True,thinking=True)
    message_to_user = []
    with open(LOGFILE, "r", encoding="utf-8") as f:
        for line in (f.readlines() [-number_of_lines:]):
            message_to_user.append(line)
    log_interaction(interaction)
    await interaction.followup.send(''.join(message_to_user),ephemeral=True)
@summonlogs.error
async def on_error(interaction: discord.Interaction, error):
    await interaction.response.defer(ephemeral=True,thinking=True)
    log_deny(interaction)
    await interaction.followup.send(
        "You do not have permissions for this command.",
        ephemeral=True
        )

@tree.command(name="shutdown_server",
              description=(f"Shutdown Server role only. "
                           "Shuts down server machine."))
async def shutdown_server(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True,thinking=True)
    log_interaction(interaction)
    role_check = False
    for role in interaction.user.roles:
        if role.name == "Shutdown Server":
            role_check = True
    if role_check == True:
        message_to_user = await ask_server("shutdown")
        await interaction.followup.send(message_to_user,ephemeral=True)
    else:
        log_deny(interaction)
        await interaction.followup.send(
            "You do not have permissions for this command.",ephemeral=True
            )

bot.run(DISCORD_TOKEN)