from nbt import nbt
from mcstatus import MinecraftServer
import os
import urllib.request
import json
import string

playerdatafolder = "/home/minecraft/minecraft/Boskrill/playerdata"


mcserver = MinecraftServer("127.0.0.1", 25565)


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


if __name__ == "__main__":
   print(getplayerpos("FreakusGeekus"))
