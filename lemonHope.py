import asyncio
import os
import random
import re

from discord.ext import commands
from dotenv import load_dotenv
from tinydb import TinyDB, Query

print('Lemon is starting')
load_dotenv()
token = os.getenv('lemonhope_token')

lemon = commands.Bot(command_prefix="Lemon, ")


def getDBFromGuild(guild):
    """
    Retrieves db from guild name
    """
    return TinyDB(r'data/' + guild + r'.json')


def isAlreadyRemembered(table, author, msg):
    """
    Determines if a quote already exists
    Returns None or quote document id
    """
    query = Query()
    results = table.search(query.name.matches('.*' + author + '.*', flags=re.IGNORECASE) and query.message == msg)

    singleResult = None

    try:
        singleResult = results[0]
    except IndexError:
        return False

    return singleResult.doc_id


async def saveQuote(table, author, message, sendResponse):
    """
    saveQuote to db
    sendResponse is the send function from discord
    """
    # qid is overloaded - but it gets the job done
    qid = isAlreadyRemembered(table, author, message)
    if not qid:
        qid = table.insert({'name': author, 'message': message})
    await sendResponse('Remembered that ' + author + ' said "' + message + '" (#' + str(qid) + ')')


def getInt(s):
    """
    Get int - helper function
    Returns int or None
    """
    try:
        return int(s)
    except ValueError:
        return None


async def saveQuote(table, author, message, sendResponse):
    if not isAlreadyRemembered(table, author, message):
        table.insert({'name': author, 'message': message})
        await sendResponse('Remembered that ' + author + ' said "' + message + '"')

def getInt(s):
    try:
        return int(s)
    except ValueError:
        return None

@lemon.event
async def on_reaction_add(reaction, user):
    if str(reaction.emoji) == '💬' and not any(r.me is True for r in reaction.message.reactions):
        print('Saving quote from ' + reaction.message.author.name + ' via reaction')

        lock = asyncio.Lock()
        quotepocket = getDBFromGuild(str(reaction.message.guild)).table('quote')
        await lock.acquire()
        try:
            await saveQuote(
                    quotepocket, reaction.message.author.name, reaction.message.content, reaction.message.channel.send)
        finally:
            lock.release()

        await reaction.message.add_reaction('💬')


@lemon.command()
async def remember(ctx, *, arg):
    split = arg.split(' ')

    name = split[0].lower()
    channel = ctx.message.channel
    findString = ''.join(split[1:]).lower()
    found = False

    print('Saving quote from ' + name + ' via text command')

    messages = await channel.history(limit=50).flatten()
    quotepocket = getDBFromGuild(str(ctx.message.guild)).table('quote')

    for ms in messages:
        if name in ms.author.name.lower() and (findString in ms.content.lower() or not findString) and "Lemon, " not in ms.content:
            lock = asyncio.Lock()
            await lock.acquire()
            try:
                await saveQuote(quotepocket, ms.author.name, ms.content, ctx.send)
            finally:
                lock.release()

            found = True
            break
    if not found:
        await ctx.send('Could not find a message from ' + name + ' containing "' + findString + '"')


@lemon.command()
async def quote(ctx, *arg):
    quotepocket = getDBFromGuild(str(ctx.message.guild)).table('quote')
    msg = None
    if len(arg) == 0:
        msg = random.choice(quotepocket.all())
    elif getInt(arg[0]):
        msg = quotepocket.get(doc_id=getInt(arg[0]))
    else:
        query = Query()
        try:
            msg = random.choice(quotepocket.search(query.name.matches('.*' + arg[0] + '.*', flags=re.IGNORECASE)))
        except IndexError:
            msg = None

    if msg:
        await ctx.send('<' + msg['name'] + '> ' + msg['message'])
    else:
        await ctx.send('Couldn\'t find that quote')


lemon.run(token)
