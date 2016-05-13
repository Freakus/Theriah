from nbt import nbt
from mcstatus import MinecraftServer
import os
import urllib.request
import json
import string
import datastore
from discord.ext import commands
import discord.utils


mcserver = MinecraftServer("127.0.0.1", 25565)
playerdatafolder = "/home/minecraft/minecraft/Boskrill/playerdata"

dimensions = {-1 : 'Nether', 0 : 'Overworld', 1 : 'End'}


class MojangAPIException(Exception):
   pass


class UnknownPlayerException(Exception):
   pass


class InvalidNameException(Exception):
   pass


allowed = frozenset(string.ascii_letters + string.digits + '_')
def checkname(name):
    return (frozenset(name) <= allowed)


def getplayeruuid(player, addheiphens=True):
    r = urllib.request.Request("https://api.mojang.com/profiles/minecraft",bytes(json.dumps([player]), "utf-8"),{"Content-Type": "application/json"})
    try:
        response = json.loads(urllib.request.urlopen(r).read().decode('utf8'))
    except:
        raise MojangAPIException
    if (len(response) > 0):
        if addheiphens == True:
            uuid = response[0]["id"][:8] + "-" + response[0]["id"][8:12] + "-" + response[0]["id"][12:16] + "-" + response[0]["id"][16:20] + "-" + response[0]["id"][20:]
            return uuid
        else:
            return response
    else:
        raise UnknownPlayerException


def getplayerpos(player):
   if not checkname(player):
       raise InvalidNameException
   uuid = getplayeruuid(player, True)
   try:
           filename = uuid + ".dat"
           nbtfile = nbt.NBTFile(os.path.join(playerdatafolder,filename),'rb')
           try:
               dim = dimensions[nbtfile['Dimension'].value]
           except AttributeError:
               dim = "Unknown Dimension"
           return(nbtfile['Pos'][0].value, nbtfile['Pos'][1].value, nbtfile['Pos'][2].value, dim)
   except FileNotFoundError:
       raise UnknownPlayerException



class MCHelper:
    bot = None

    def __init__(self, bot):
        self.bot = bot

    @commands.bot.command(pass_context=True)
    async def status(self, ctx):
        try:
            status = mcserver.status()
            await self.bot.say("Boskrill has {0} player(s) and replied in {1} ms".format(status.players.online, status.latency))
        except:
            await self.bot.say("Boskrill is currently not responding!")


    @commands.bot.command(pass_context=True)
    async def online(self, ctx):
        try:
            status = mcserver.query()
            #await self.bot.say("Boskrill has {0} players and replied in {1} ms".format(status.players.online, status.latency))
            await self.bot.say("{0} has {1} player(s) online:\n{2}".format(status.map, status.players.online, ", ".join(status.players.names)))
        except:
            await self.bot.say("Boskrill is currently not responding!")


    @commands.bot.command(pass_context=True)
    async def location(self, ctx, player : str):
        """Get a player's coordinates and dimension."""
        try:
            pos = getplayerpos(player)
            dim = 0
            if pos[3] == "Nether":
                dim = 1
            elif pos[3] == "End":
                dim = 2
            await self.bot.say("%s was last seen at %d %d %d in the %s\n--> " % (player, pos[0], pos[1], pos[2], pos[3]) + mapurl % (pos[0], pos[1], pos[2], dim))
        except UnknownPlayerException:
            await self.bot.say(errormessages['unknownplayer'])
        except MojangAPIException:
            await self.bot.say(errormessages['http'])
        except InvalidNameException:
            await self.bot.say(errormessages['invalidplayer'])


    @commands.group(pass_context=True, invoke_without_command=True)
    @commands.has_role('op')
    async def whitelist(self, ctx):
        """Manage the whitelist."""
        if ctx.invoked_subcommand is None:
            await self.bot.say('What do you want me to do with the whitelist?')


    @whitelist.command(pass_context=True)
    @commands.has_role('op')
    async def add(self, name : str):
        """Add someone to the whitelist."""
        if (0 < len(name) <= 16) and checkname(name) and name is not None:
            await self.bot.say('This will eventually add {0} to the whitelist'.format(name))
        else:
            await self.bot.say(errormessages['unknownplayer'])


    @whitelist.command(pass_context=True)
    @commands.has_role('op')
    async def remove(self, name : str):
        """Remove someone from the whitelist."""
        if (0 < len(name) <= 16) and checkname(name) and name is not None:
            await self.bot.say('This will eventually remove {0} from the whitelist'.format(name))
        else:
            await self.bot.say(errormessages['unknownplayer'])



def setup(bot):
    bot.add_cog(MCHelper(bot))


if __name__ == "__main__":
   print(getplayerpos("FreakusGeekus"))
