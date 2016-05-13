import logging
logging.basicConfig(level=logging.INFO)

import json

import discord
from discord.ext import commands
import random

from discord.errors import *
from discord.enums import ChannelType

import datastore
import tags

TOKEN = "Token"
CLIENT_ID = 9999999999999

mapurl = "http://freakus.me/~minecraft/map/#/%d/%d/%d/max/0/%d"

errormessages = {
    'forbidden' : "I'm sorry, I can't do that.",
    'http' : "Did someone cast an anti-magic field?",
    'unknown' : "Stop trying to use wild magic you fool!",
    'notimplemented' : "Sorry. I haven't learned how to do that yet.",
    'ambiguousmember' : "I'm not sure who you mean...",
    'unknownmember' : "I don't know of anyone with that name...",
    'ambiguouschannel' : "I'm not sure which channel you mean...",
    'unknownchannel' : "I don't know of any such channel...",
    'ambiguousrole' : "I'm not sure which role you mean...",
    'unknownrole' : "I don't think that's an actual role...",
    'unknownplayer' : "Sorry, I don't know who that is.",
    'invalidplayer' : "Player names can only contain letters, numbers, and underscores."
}


class UnknownRoleException(Exception):
    pass




class AmbiguousRoleException(Exception):
    pass




class UnknownChannelException(Exception):
    pass




class AmbiguousChannelException(Exception):
    pass




class UnknownMemberException(Exception):
    pass




class AmbiguousMemberException(Exception):
    pass


class MissingAuth(Exception):
    pass



description = '''A friendly magical otter from the village of Boskrill.
There are a number of things he can do for you:'''
bot = commands.Bot(command_prefix=commands.when_mentioned_or('?'), description=description, pm_help=True)
bot.load_extension('tags')
bot.load_extension('mchelper')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print(discord.utils.oauth_url(CLIENT_ID, permissions=None))
    print('------')
    for s in bot.servers:
        print(s.name)
        print(', '.join([str(channel) for channel in s.channels]))
    print('------')




@bot.command(hidden=True)
async def seticon():
    with open('TheriahRiptideIconTransparent.png', 'rb') as f:
        await bot.edit_profile(avatar=f.read())
        seticon.enabled = False
        await bot.say("Done.")




@bot.command()
async def roll(dice : str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await bot.say('Format has to be in NdN!')
        return


    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await bot.say(result)




@bot.command(description='For when you wanna settle the score some other way')
async def choose(*choices : str):
    """Chooses between multiple choices."""
    await bot.say(random.choice(choices))




@bot.command()
async def joined(member : discord.Member):
    """Says when a member joined."""
    await bot.say('{0.name} joined in {0.joined_at}'.format(member))




@bot.group(pass_context=True, invoke_without_command=True)
@commands.has_role('Admin')
async def role(ctx):
    """Manage roles."""
    if ctx.invoked_subcommand is None:
        await bot.say('What do you want me to do with roles?')




@role.command(pass_context=True)
@commands.has_role('Admin')
async def grant(ctx):
    """Grants a role to the specified user."""
    try:
        members = list(ctx.message.mentions)
        if len(members) > 1:
            raise AmbiguousMemberException
        elif len(members) < 1:
            raise UnknownMemberException
        
        await bot.say("What role should I grant to {0}?".format(members[0].name))
        # Get a reply from the user stating what role to grant
        reply = await bot.wait_for_message(timeout=20,author=ctx.message.author)
        
        roles = list((role for role in ctx.message.server.roles if role.name==reply.content))
        if len(roles) > 1:
            raise AmbiguousRoleException
        elif len(roles) < 1:
            raise UnknownRoleException
        else:
            await bot.add_roles(members[0], roles[0])
            await bot.say("Done!")
        
    except UnknownMemberException:
        await bot.say(errormessages['unknownmember'])
    except AmbiguousMemberException:
        await bot.say(errormessages['ambiguousmember'])
    except UnknownRoleException:
        await bot.say(errormessages['unknownrole'])
    except AmbiguousRoleException:
        await bot.say(errormessages['ambiguousrole'])
    except Forbidden:
        await bot.say(errgormessages['forbidden'])
    except HTTPException:
        await bot.say(errormessages['http'])
    except Exception:
        await bot.say(errormessages['unknown'])




@role.command(pass_context=True)
@commands.has_role('Admin')
async def revoke(ctx):
    """Revokes a role from the specified user."""
    try:
        members = list(ctx.message.mentions)
        if len(members) > 1:
            raise AmbiguousMemberException
        elif len(members) < 1:
            raise UnknownMemberException
        
        await bot.say("What role should I remove from {0}?".format(members[0].name))
        # Get a reply from the user stating what role to remove
        reply = await bot.wait_for_message(timeout=20, author=ctx.message.author)
        
        roles = list((role for role in ctx.message.server.roles if role.name==reply.content))
        if len(roles) > 1:
            raise AmbiguousRoleException
        elif len(roles) < 1:
            raise UnknownRoleException
        else:
            await bot.remove_roles(members[0], roles[0])
            await bot.say("Done!")
        
    except UnknownMemberException:
        await bot.say(errormessages['unknownmember'])
    except AmbiguousMemberException:
        await bot.say(errormessages['ambiguousmember'])
    except UnknownRoleException:
        await bot.say(errormessages['unknownrole'])
    except AmbiguousRoleException:
        await bot.say(errormessages['ambiguousrole'])
    except Forbidden:
        await bot.say(errormessages['forbidden'])
    except HTTPException:
        await bot.say(errormessages['http'])
    except Exception:
        await bot.say(errormessages['unknown'])




@bot.group(pass_context=True, invoke_without_command=False)
@commands.has_role('Admin')
async def kick(ctx):
    """Kicks (or bans) the specified user."""
    if ctx.invoked_subcommand is not None:
        return
    try:
        members = list(ctx.message.mentions)
        if len(members) > 1:
            raise AmbiguousMemberException
        elif len(members) < 1:
            raise UnknownMemberException
        await bot.kick(members[0])
        await bot.say("Done!")


    except UnknownMemberException:
        await bot.say(errormessages['unknownmember'])
    except AmbiguousMemberException:
        await bot.say(errormessages['ambiguousmember'])
    except Forbidden:
        await bot.say(errormessages['forbidden'])
    except HTTPException:
        await bot.say(errormessages['http'])
    except Exception:
        await bot.say(errormessages['unknown'])




@kick.command(pass_context=True)
@commands.has_role('Admin')
async def ban(ctx, days : int):
    """Bans the specified user."""
    try:
        members = list(ctx.message.mentions)
        if len(members) > 1:
            raise AmbiguousMemberException
        elif len(members) < 1:
            raise UnknownMemberException
        if days is None:
            days = 0
        elif days > 7:
            days = 7
            await bot.say("I can't erase anchient history! I'll do the past week for you, as that's the best I can.")
        await bot.ban(members[0], days)
        await bot.say("Done!")


    except UnknownMemberException:
        await bot.say(errormessages['unknownmember'])
    except AmbiguousMemberException:
        await bot.say(errormessages['ambiguousmember'])
    except Forbidden:
        await bot.say(errormessages['forbidden'])
    except HTTPException:
        await bot.say(errormessages['http'])
    except Exception:
        await bot.say(errormessages['unknown'])




@bot.group(pass_context=True, aliases=['channel'])
@commands.has_role('Admin')
async def room(ctx):
    """Manage channels."""
    if ctx.invoked_subcommand is None:
        await bot.say('What do you want me to do with regards to channels?')




@room.command(pass_context=True)
@commands.has_role('Admin')
async def addText(ctx, channel : str):
    """Creates a new text Channel."""
    try:
        await bot.create_channel(ctx.message.server, channel, type=ChannelType.text)
        await bot.say("Done!")
    except Forbidden:
        await bot.say(errormessages['forbidden'])
    except HTTPException:
        await bot.say(errormessages['http'])
    except Exception:
        await bot.say(errormessages['unknown'])




@room.command(pass_context=True)
@commands.has_role('Admin')
async def addVoice(ctx, channel : str):
    """Creates a new voice Channel."""
    try:
        await bot.create_channel(ctx.message.server, channel, type=ChannelType.voice)
        await bot.say("Done!")
    except Forbidden:
        await bot.say(errormessages['forbidden'])
    except HTTPException:
        await bot.say(errormessages['http'])
    except Exception:
        await bot.say(errormessages['unknown'])




@room.command(pass_context=True)
@commands.has_role('Admin')
async def remove(ctx, channelname : str):
    """Deletes a channel."""
    try:
        channels = list((channel for channel in ctx.message.server.channels if channel.name==channelname))
        if len(channels) > 1:
            raise AmbiguousChannelException
        elif len(channels) < 1:
            raise UnknownChannelException

        await bot.say("You're absolutely sure, yes?")
        reply = await bot.wait_for_message(timeout=20, author=ctx.message.author)
        if reply is None or reply.content != "yes":
            await bot.say("I thought not.")
            return

        await bot.say("Are you _REALLY_?")
        reply = await bot.wait_for_message(timeout=20, author=ctx.message.author)
        if reply is None or reply.content != "yes":
            await bot.say("Don't waste my time then!")
            return
        await bot.delete_channel(channels[0])
        await bot.say("Done!")
    except UnknownChannelException:
        await bot.say(errormessages['unknownchannel'])
    except AmbiguousChannelException:
        await bot.say(errormessages['ambiguouschannel'])
    except Forbidden:
        await bot.say(errormessages['forbidden'])
    except HTTPException:
        await bot.say(errormessages['http'])
    except Exception:
        await bot.say(errormessages['unknown'])




@bot.command()
async def img(board : str, search : str):
    """Searches an image board and returns the top result."""
    try:
        await bot.say(errormessages['notimplemented'])
    except Forbidden:
        await bot.say(errormessages['forbidden'])
    except HTTPException:
        await bot.say(errormessages['http'])
    except Exception:
        await bot.say(errormessages['unknown'])

try:
    with open('auth.json', 'r') as fp:
        auth = json.load(fp)
        if "CLIENT_ID" in auth:
            CLIENT_ID = auth["CLIENT_ID"]
        else:
            raise MissingAuth
        if "TOKEN" in auth:
            TOKEN = auth["TOKEN"]
        else:
            raise MissingAuth
except (json.JSONDecodeError, MissingAuth, FileNotFoundError):
    with open('auth.json', 'w') as fp:
        json.dump({"CLIENT_ID": CLIENT_ID, "TOKEN": TOKEN}, fp)
    print("No Client ID and/or Token found!\nPlease update auth.json with the relevant details.")
    quit()

try:
    bot.run(TOKEN)
except discord.errors.HTTPException as e:
    print(e)
