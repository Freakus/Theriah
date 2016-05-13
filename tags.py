import datastore
import json

from discord.ext import commands
import discord.utils

import checks


class OwnerError(Exception):
    pass

class formats:
    async def entry_to_code(bot, entries):
        width = max(map(lambda t: len(t[0]), entries))
        output = ['```']
        fmt = '{0:<{width}}: {1}'
        for name, entry in entries:
            output.append(fmt.format(name, entry, width=width))
        output.append('```')
        await bot.say('\n'.join(output))


class Tag:
    _ownerid = ""
    _title   = ""
    _content = ""
    _uses    = 0

    def __init__(self, ownerid, title, content, **kwargs):
        self._ownerid = ownerid
        self._title   = title
        self._content = content
        self._uses    = kwargs.pop('uses', 0)

    def __str__(self):
        return self._content

    def __contains__(self, key):
        key = key.lower()
        if key in self._title.lower() or key in self._content.lower():
            return True
        else:
            return False

    @property
    def ownerid(self):
        return self._ownerid

    @property
    def searchtitle(self):
        return self._title.lower()

    @property
    def title(self):
        return self._title

    @property
    def searchcontent(self):
        return self._content.lower()

    @property
    def content(self):
        return self._content

    @property
    def uses(self):
        return self._uses

    def query(self):
        self._uses += 1
        return self

class TagEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Tag):
            data = obj.__dict__.copy()
            data.update({"__tag__": True})
            return data
        return json.JSONEncoder.default(self, obj)

def tag_decoder(obj):
    if '__tag__' in obj:
        return Tag(ownerid=obj['_ownerid'], title=obj['_title'], content=obj['_content'], uses=obj['_uses'])
    return obj

class TagStore:
    _storage = {}
    bot = None
    
    def __init__(self, bot):
        self.bot = bot
    
    def _getscope(self, serverid, channelid):
        scope = "tags-%s-%s" % (serverid, channelid)
        if scope not in self._storage:
            self._storage[scope] = datastore.DataStore(scope, TagEncoder, tag_decoder)
        return self._storage[scope]

    def search(self, serverid, channelid, keyword, limit=10):
        results = []
        for k,tag in sorted(self._getscope(serverid, channelid).items(), key = lambda x: (x[1].uses, x[1].searchtitle), reverse = True):
            limit -= 1
            if keyword in tag:
                results += [tag.title]
            if limit == 0:
                break
        return results

    def insert(self, serverid, channelid, ownerid, title, content):
        self._getscope(serverid, channelid).insert(title, Tag(ownerid = ownerid, title = title, content = content))

    def update(self, serverid, channelid, ownerid, title, content):
        scope = self._getscope(serverid, channelid)
        tag = scope.select(title)
        if ownerid == tag.ownerid or ownerid is None:
            scope.update(title, Tag(ownerid = tag.ownerid, title = title, content = content, uses = tag.uses))
        else:
            raise OwnerError

    def delete(self, serverid, channelid, ownerid, title):
        scope = self._getscope(serverid, channelid)
        tag = scope.select(title)
        if ownerid == tag.ownerid or ownerid is None:
            scope.delete(title)
        else:
            raise OwnerError

    def select(self, serverid, channelid, title):
        title = title.lower()
        scope = self._getscope(serverid, channelid)
        tag = scope.select(title).query()
        scope.sync()
        return tag

    def exists(self, serverid, channelid, title):
        try:
            self._getscope(serverid, channelid).select(title)
            return True
        except KeyError:
            return False


    @commands.group(pass_context=True, invoke_without_command=True, no_pm=True)
    async def tag(self, ctx, *, name : str):
        """Allows you to tag text for later retrieval.

        If a subcommand is not called, then this will search the tag database
        for the tag requested.
        """
        channel = ctx.message.channel.id
        server = ctx.message.server.id
        try:
            tag = self.select(server, channel, name)
            await self.bot.say("{}```\n{}\n```".format(tag.title, str(tag)))
        except KeyError:
            await self.bot.say('Tag "{}" not found.'.format(name))

    @tag.error
    async def tag_error(self, error, ctx):
        if isinstance(error, commands.MissingRequiredArgument):
            await self.bot.say('You need to pass in a tag name.')

    def verify_lookup(self, lookup):
        lookup = lookup.lower().strip()
        if '@everyone' in lookup:
            raise RuntimeError('That tag is using blocked words.')

        if not lookup:
            raise RuntimeError('You need to actually pass in a tag name.')

        if len(lookup) > 100:
            raise RuntimeError('Tag name is a maximum of 100 characters.')

    @tag.command(pass_context=True, aliases=['add'], no_pm=True)
    async def create(self, ctx, name : str, *, content : str):
        """Creates a new tag owned by you.
        
        The tag you create can only be accessed in the channel that it was created in.
        """
        content = content.replace('@everyone', '@\u200beveryone')
        try:
            self.verify_lookup(name)
        except RuntimeError as e:
            await self.bot.say(e)
            return

        try:
            self.insert(ctx.message.server.id, ctx.message.channel.id, ctx.message.author.id, name, content)
            await self.bot.say('Tag "{}" successfully created.'.format(name))
        except KeyError:
            await self.bot.say('A tag with the name of "{}" already exists.'.format(name))
        

    @tag.command(pass_context=True, no_pm=True)
    async def make(self, ctx):
        """Interactive makes a tag for you.

        This walks you through the process of creating a tag with
        its name and its content. This works similar to the tag
        create command.
        """
        message = ctx.message
        await self.bot.say('Hello. What would you like the name tag to be?')

        def check(msg):
            try:
                self.verify_lookup(msg.content.lower())
                return True
            except:
                return False

        name = await self.bot.wait_for_message(author=message.author, channel=message.channel, timeout=60.0, check=check)
        if name is None:
            await self.bot.say('You took too long. Goodbye.')
            return

        if self.exists(message.server.id, message.channel.id, name.content):
            fmt = 'Sorry. A tag with that name exists already. Redo the command {0.prefix}tag make.'
            await self.bot.say(fmt.format(ctx))
            return

        await self.bot.say('Alright. So the name is {0.content}. What about the tag\'s content?'.format(name))
        content = await self.bot.wait_for_message(author=name.author, channel=name.channel, timeout=300.0)
        if content is None:
            await self.bot.say('You took too long. Goodbye.')
            return

        if len(content.content) == 0 and len(content.attachments) > 0:
            # we have an attachment
            content = content.attachments[0].get('url', '*Could not get attachment data*')
        else:
            content = content.content.replace('@everyone', '@\u200beveryone')

        try:
            self.insert(message.server.id, message.channel.id, message.author.id, name.content, content)
            await self.bot.say('Cool. I\'ve made your {0.content} tag.'.format(name))
        except KeyError:
            await self.bot.say('Looks like someone beat you to making a {0.content} tag, sorry. Try again.'.format(name))

    def generate_stats(self, db, label):
        yield '- Total {} tags: {}'.format(label, len(db))
        if db:
            popular = sorted(db.values(), key=lambda t: (t.uses, t.searchtitle), reverse=True)
            total_uses = sum(t.uses for t in popular)
            yield '- Total {} tag uses: {}'.format(label, total_uses)
            for i, tag in enumerate(popular[:3], 1):
                yield '- Rank {0} tag: {1.name} with {1.uses} uses'.format(i, tag)

    # @tag.command(pass_context=True, no_pm=True)
    # async def stats(self, ctx):
        # """Gives stats about the tag database."""
        # result = []
        # channel = ctx.message.channel.id
        # generic = self.config.get('generic', {})
        # # result.extend(self.generate_stats(generic, 'Generic'))

        # if channel is not None:
            # result.extend(self.generate_stats(self.config.get(channel.id, {}), 'Channel Specific'))

        # await self.bot.say('\n'.join(result))

    @tag.command(pass_context=True, no_pm=True)
    async def edit(self, ctx, name : str, *, content : str):
        """Modifies an existing tag that you own.

        This command completely replaces the original text.
        """

        content = content.replace('@everyone', '@\u200beveryone')
        channel = ctx.message.channel.id
        server = ctx.message.server.id
        ownerid = ctx.message.author.id
        try:
            self.update(server, channel, ownerid, name, content)
            await self.bot.say('Tag successfully edited.')
        except KeyError:
            await self.bot.say('The tag does not exist.')
        except OwnerError:
            await self.bot.say('Only the tag owner can edit this tag.')



    @tag.command(pass_context=True, aliases=['delete'], no_pm=True)
    async def remove(self, ctx, *, name : str):
        """Removes a tag that you own.

        The tag owner can always delete their own tags. If someone requests
        deletion and has Manage Messages permissions or a Bot Mod role then
        they can also remove tags.
        """
        server = ctx.message.server.id
        channel = ctx.message.channel.id
        ownerid = ctx.message.author.id

        can_delete = any((True for role in ctx.message.author.roles if role.name=='Admin')) or checks.is_owner_check(ctx.message) or checks.check_permissions(ctx, manage_messages=True)

        if can_delete:
            ownerid = None

        try:
            self.delete(server, channel, ownerid, name)
            await self.bot.say('Tag successfully removed.')
        except:
            await self.bot.say('You do not have permissions to delete this tag.')

    # @tag.command(pass_context=True, no_pm=True)
    # async def info(self, ctx, *, name : str):
        # """Retrieves info about a tag.

        # The info includes things like the owner and how many times it was used.
        # """

        # channel = ctx.message.channel
        # server = ctx.message.server
        # tag = self.select(server, channel, name)

        # if tag is None:
            # await self.bot.say('Tag not found.')
            # return

        # entries = tag.info_entries(ctx, self.get_possible_tags(channel))
        # await formats.entry_to_code(self.bot, entries)

    # @info.error
    # async def info_error(self, error, ctx):
        # if isinstance(error, commands.MissingRequiredArgument):
            # await self.bot.say('Missing tag name to get info of.')

    # @tag.command(name='list', pass_context=True, no_pm=True)
    # async def _list(self, ctx, *, member : discord.Member = None):
        # """Lists all the tags that belong to you or someone else.
        # """

        # owner = ctx.message.author if member is None else member
        # channel = ctx.message.channel
        # tags = [tag.name for tag in self.config.get('generic', {}).values() if tag.owner_id == owner.id]
        # if channel is not None:
            # tags.extend(tag.name for tag in self.config.get(channel.id, {}).values() if tag.owner_id == owner.id)

        # if tags:
            # fmt = '{0.name} has the following tags:\n{1}'
            # await self.bot.say(fmt.format(owner, ', '.join(tags)))
        # else:
            # await self.bot.say('{0.name} has no tags.'.format(owner))

    @tag.command(name='search', pass_context=True, no_pm=True)
    async def _search(self, ctx, *, query : str):
        """Searches for a tag.
        
        The query must be at least 2 characters.
        """

        limit = 10;
        server = ctx.message.server.id
        channel = ctx.message.channel.id
        if len(query) < 2:
            await self.bot.say('The query length must be at least two characters.')
            return

        results = self.search(server, channel, query, limit)
        fmt = ''
        if len(results) == limit:
            fmt = 'At least {} tag(s) found.\n{}'
        else:
            fmt = '{} tag(s) found.\n{}'
        
        if results:
            await self.bot.say(fmt.format(len(results), ', '.join(results)))
        else:
            await self.bot.say('No tags found.')




def setup(bot):
    bot.add_cog(TagStore(bot))

