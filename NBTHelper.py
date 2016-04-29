from nbt import nbt
import os
import urllib.request
import json
import string

playerdatafolder = "/home/minecraft/minecraft/Boskrill/playerdata"



allowed = frozenset(string.ascii_letters + string.digits + '_')

def MCCheckName(name):
    return (frozenset(name) <= allowed)


class MojangAPIException(Exception):
    pass

class UnknownPlayerException(Exception):
    pass

dimensions = {-1 : 'Nether', 0 : 'Overworld', 1 : 'End'}

def MCGetPlayerPos(player):
    r = urllib.request.Request("https://api.mojang.com/profiles/minecraft",bytes(json.dumps([player]), "utf-8"),{"Content-Type": "application/json"})
    try:
        response = json.loads(urllib.request.urlopen(r).read().decode('utf8'))
    except:
        raise MojangAPIException
    try:
        if (len(response) > 0):
            filename = response[0]["id"][:8] + "-" + response[0]["id"][8:12] + "-" + response[0]["id"][12:16] + "-" + response[0]["id"][16:20] + "-" + response[0]["id"][20:] + ".dat"
            print(filename)
            nbtfile = nbt.NBTFile(os.path.join(playerdatafolder,filename),'rb')
            dim = dimensions[nbtfile['Dimension'].value]
            return(nbtfile['Pos'][0].value, nbtfile['Pos'][1].value, nbtfile['Pos'][2].value, dim)
        else:
            raise UnknownPlayerException
    except:
        raise UnknownPlayerException


if __name__ == "__main__":
    print(MCGetPlayerPos("FreakusGeekus"))
