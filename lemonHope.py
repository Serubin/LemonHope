import random
import os
from discord.ext import commands
from tinydb import TinyDB, Query
from dotenv import load_dotenv
import asyncio
import re

load_dotenv()
token = os.getenv('lemonhope_token')

lemon = commands.Bot(command_prefix="Lemon, ")


def getDBFromGuild(guild):
    return TinyDB(r'data/' + guild + r'.json')


def isAlreadyRemembered(table, author, msg):
    query = Query()
    return any(table.search(query.name.matches('.*' + author + '.*', flags=re.IGNORECASE) and query.message == msg))


@lemon.event
async def on_reaction_add(reaction, user):
    if str(reaction.emoji) == '💬' and not any(r.me is True for r in reaction.message.reactions):
        await reaction.message.add_reaction('💬')
        lock = asyncio.Lock()
        await lock.acquire()
        try:
            quotepocket = getDBFromGuild(str(reaction.message.guild)).table('quote')
            if not isAlreadyRemembered(quotepocket, reaction.message.author.name, reaction.message.content):
                quotepocket.insert({'name': reaction.message.author.name, 'message': reaction.message.content})
                await reaction.message.channel.send(
                    'Remembered that ' + reaction.message.author.name + ' said ' + reaction.message.content)
        finally:
            lock.release()


@lemon.command()
async def remember(ctx, *, arg):
    split = arg.split(' ')
    name = split[0]
    channel = ctx.message.channel
    findString = ''.join(split[1:])
    messages = await channel.history(limit=50).flatten()
    found = False
    quotepocket = getDBFromGuild(str(ctx.message.guild)).table('quote')
    for ms in messages:
        if name in ms.author.name and (findString in ms.content or not findString) and "Lemon, " not in ms.content:
            lock = asyncio.Lock()
            await lock.acquire()
            try:
                if not isAlreadyRemembered(quotepocket, ms.author.name, ms.content):
                    quotepocket.insert({'name': ms.author.name, 'message': ms.content})
                    await ctx.send('Remembered that ' + ms.author.name + ' said "' + ms.content + '"!')
            finally:
                lock.release()
            found = True
            break
    if not found:
        await ctx.send('Could not find a message from ' + name + ' containing ' + findString)


@lemon.command()
async def quote(ctx, *arg):
    quotepocket = getDBFromGuild(str(ctx.message.guild)).table('quote')
    if len(arg) == 0:
        msg = random.choice(quotepocket.all())
        await ctx.send('<' + msg['name'] + '> ' + msg['message'])
    else:
        query = Query()
        msg = random.choice(quotepocket.search(query.name.matches('.*' + arg[0] + '.*', flags=re.IGNORECASE)))
        await ctx.send('<' + msg['name'] + '> ' + msg['message'])


lemon.run(token)
