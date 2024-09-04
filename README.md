This is a collection of scripts I use to allow people in my Discord channel to turn on dedicated servers for specific games with slash commands. The end result is I don't have to leave a machine online 24/7 hosting a dedicated server, yet people in my Discord server can use a slash command such as /summonpalworld and within minutes be able to connect to my Palworld dedicated server. 

But in a little more detail:

The summonerbot.py script is a Discord bot/app and can be run on any computer on my LAN whenever I want the dedicated server computer to be available to be turned on. The bot makes slash commands available in the Discord server for each game's dedicated server I've set up on my dedicated server computer. When the slash commands are used, the computer hosting the bot will wake up the dedicated server computer on the LAN, which will start up running DedicatedServerController.py. DedicatedServerController.py will reply to requests from the machine hosting the bot and take actions to start Linux services for the dedicated server and automatic save backups specific to the game requested. 

Overall, this makes my dedicated server setup very flexible and automated, while maximizing downtime to conserve power consumption. 
