#!/usr/bin/env python3
# coding: utf-8

import asyncio
import json
from email.mime.text import MIMEText
from queue import Queue
from random import choice
from sys import exit

import aiosmtplib
import discord
from chatterbot import ChatBot
from discord.ext.commands import Bot

from settings import read_settings, create_new_settings

# Discord bot initialization
# client = discord.Client()
description = '''Moby serves to protect, as well as be the host of the hit online series, the
Adventures of Tim and Moby!'''
MobyBot = Bot(command_prefix='!', description=description)

# Load settings file
options = {}
try:
    options = read_settings('settings.txt')
except:
    create_new_settings()
    print('Please configure the settings.txt file.')
    exit()

# "unpack" settings file
chat_bot_name = options['chat_bot_name']
bot_token = options['bot_token']
email_username = options['email_username']
email_password = options['email_password']
email_address = options['email_address']
email_smtp = options['email_smtp']
email_port = int(options['email_port'])
cowan_text_gateway = options['cowan_text_gateway']
client_email = options['client_email']
client_password = options['client_password']

yt_player_opts = {'default_search': 'auto'}
yt_player_before_args = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"

# init chatterbot
chatbot = ChatBot(chat_bot_name, trainer='chatterbot.trainers.ChatterBotCorpusTrainer')
chatbot.train("chatterbot.corpus.english")

loop = asyncio.get_event_loop()


class BotStates:
    def __init__(self):
        # states that the bot can be in
        self.annoying_mode = False      # responding to all messages with !chat?
        self.voice_client = None        # current voice client for sounds
        self.player = None              # current sound player
        self.volume = 0.8               # volume of sound player
        self.sound_queue = Queue()      # songs queued

        self.locked = False              # admin only mode


bot_states = BotStates()


async def jukebox():
    """
    A simple playlist manager function, designed to run
    concurrently and constantly.
    :return: None
    """
    # don't start until the bot is logged in
    await MobyBot.wait_until_ready()
    # only run while the bot is active
    while not MobyBot.is_closed:
        await asyncio.sleep(1)  # task runs every n seconds
        if bot_states.sound_queue.empty():
            pass    # do nothing if there are no songs in the queue
        elif bot_states.sound_queue.not_empty:
            # continue if there is a player active and there are no songs in the queue
            if bot_states.player is not None:
                # once the song is done...
                if bot_states.player.is_done():
                    # start playing next song in queue
                    url = bot_states.sound_queue.get()
                    bot_states.player = await bot_states.voice_client.create_ytdl_player(
                        url=url,
                        ytdl_options=yt_player_opts,
                        before_options=yt_player_before_args)
                    bot_states.player.start()
                    # state song change
                    await MobyBot.say('Now playing - {0.title}.'.format(bot_states.player))
                    await MobyBot.change_presence(game=discord.Game(name=bot_states.player.title))
        else:   # otherwise just say that he's on brainpop
            await MobyBot.change_presence(game=discord.Game(name='Brainpop.com'))


# add the looping event to the bot
MobyBot.loop.create_task(jukebox())


@MobyBot.event
async def on_ready():
    """
    Runs when the bot joins the server and is ready to respond to requests.
    Currently, Moby just outputs to the console that he is ready.
    :return: None
    """
    print('Connected!')
    print('Username: ' + MobyBot.user.name)
    print('ID: ' + MobyBot.user.id)

    await MobyBot.login(bot_token)
    await MobyBot.change_presence(game=discord.Game(name='Brainpop.com'))


@MobyBot.event
async def on_message(message):
    """
    Does stuff on message sent
    :param message: the message object itself
    :return: none
    """

    # do a command
    if message.content.startswith('!'):
        if not bot_states.locked or message.author.permissions_in(message.channel).administrator:
            return await MobyBot.process_commands(message)
        else:
            return await MobyBot.send_message(message.channel, "Only admins can issue commands right now.")

    else:
        # ensure bot doesn't respond to self in annoyingmode
        if bot_states.annoying_mode and message.author.name != "Moby":
            # get response
            response = chatbot.get_response(message.content)
            print("[Command] ({0}) chat \"{1}\"->\"{2}\"".format(message.author.name,
                                                                 message.content,
                                                                 response))
            return await MobyBot.send_message(message.channel, response)


@MobyBot.command(
    pass_context=True,
    description="Toggles whether or not Moby will reply to everything in the channel.")
async def annoyingmode(ctx):
    """
    Toggles whether or not Moby will reply to everything in the channel.
    Usage: !annoyingmode
    
    :param ctx: Discord context
    :return: None
    """
    print("[Command] ({0}) annoyingmode".format(ctx.message.author.name))

    if bot_states.annoying_mode:
        bot_states.annoying_mode = False
        return await MobyBot.send_message(ctx.message.channel, "Annoying mode off.")

    else:
        bot_states.annoying_mode = True
        return await MobyBot.send_message(ctx.message.channel, "Annoying mode on.")


@MobyBot.command(
    pass_context=True,
    description="Send a message to Moby's chat bot feature.")
async def chat(ctx, *args):
    """
    Send a message to Moby's chat bot feature.
    
    :param ctx: Discord context
    :param args: all text following !chat
    :return: None
    """
    # create the string message
    msg = ' '.join(args)
    # get response
    response = chatbot.get_response(msg)

    print("[annoyingmode] ({0}) chat \"{1}\"->\"{2}\"".format(ctx.message.author.name, msg, response))

    # Moby speaks
    return await MobyBot.say(response)


@MobyBot.command(
    pass_context=True,
    description="Randomly select one of the following options separated by spaces.")
async def choose(ctx, *choices: str):
    """
    Choose between multiple choices separated by spaces.
    Usage: !choice choice1 choice2 choice3 ... choicen
    :param ctx: Discord context
    :param choices: words following the command
    :return: None
    """
    print("[Command] ({0}) choices {1}".format(ctx.message.author.name, choices))

    return await MobyBot.say(choice(choices))


@MobyBot.command(
    pass_context=True,
    description="Send an email from Moby. Usage: !email email@email.com words in message")
async def email(ctx, *args):
    """
    Send an email from Moby.
    Usage: !email email@email.com words in message
    
    :param ctx: Context
    :param args: Everything following the command, which is put into a MIME-formatted email.
    :return: None
    """

    print("[Command] ({0}) email".format(ctx.message.author.name))

    # create message by concatenating string
    text = ' '.join(args[1:])
    text += "\n\n\n-----\nThis email was sent by a bot named Moby in a Discord channel."
    text += "\n{0} ordered that this email be sent to you.".format(ctx.message.author.name)
    message = MIMEText(text)
    message['From'] = email_address
    message['To'] = args[0]
    message['Subject'] = "A message from Moby"

    # init email stuff, connects to the server only when needed
    smtp = aiosmtplib.SMTP(hostname=email_smtp, port=email_port, loop=loop, use_tls=False)
    await smtp.connect()
    await smtp.ehlo()
    await smtp.starttls()
    await smtp.ehlo()
    await smtp.login(email_username, email_password)

    try:
        await smtp.send_message(message)
        await MobyBot.say('{0.author.mention} Email sent.'.format(ctx.message))
    except aiosmtplib.SMTPException:
        await MobyBot.say('{0.author.mention} Failed to send email.'.format(ctx.message))

    # close the connection to the server
    smtp.close()


@MobyBot.command(
    pass_context=True,
    description="Say hi to Moby and Moby says hi back.")
async def hello(ctx):
    """
    Say hi to Moby and Moby says hi back.
    Usage: !hello
    
    :param ctx: Context
    :return: None
    """
    print("[Command] ({0}) hello".format(ctx.message.author.name))

    msg = 'Hello {0.author.mention}'.format(ctx.message)
    return await MobyBot.send_message(ctx.message.channel, msg)


@MobyBot.command(
    pass_context=True,
    description="Tell a random joke. Quality not assured.")
async def joke(ctx):
    """
    Tell a random joke. Quality not assured.
    Usage: !joke
    
    :param ctx: Context
    :return: None
    """

    print("[Command] ({0}) joke".format(ctx.message.author.name))

    with open('jokes.json') as f:
        jokes = json.load(f)
        j = choice(jokes)['body']
        while str.strip(j) == '':
            j = choice(jokes)['body']

        str.strip(j)

        msg = '{0.author.mention}, here\'s one for ya!:\n{1}'.format(ctx.message, j)
        return await MobyBot.send_message(ctx.message.channel, msg, tts=True)


@MobyBot.command(
    pass_context=True,
    description="Toggles admin lock on the bot.")
async def lock(ctx):
	"""
	Toggles admin lock on the bot.
	Usage: !lock
	"""
    author = ctx.message.author
    channel = ctx.message.channel

    if author.permissions_in(channel).administrator:
        bot_states.locked = not bot_states.locked
        print("[Command] ({0}) lock {1}".format(author.name, bot_states.locked))
        return await MobyBot.say('{0.author.mention} Admin lock changed to: {1}.'.format(
            ctx.message, bot_states.locked))
    else:
        return await MobyBot.say('{0.author.mention} You don\'t have permissions.'.format(ctx.message))





@MobyBot.command(
    pass_context=True,
    description="Pauses the currently playing song.")
async def pause(ctx, *args):
    """
    Pauses the currently playing song.
    Usage: !pause
    A song must be playing for this to work.
    
    :param ctx: Discord context
    :return: None
    """
    if (bot_states.player is None) or bot_states.player.is_done():
        return await MobyBot.say('{0.author.mention} Nothing is playing.'.format(ctx.message))
    elif bot_states.player.is_playing():
        bot_states.player.pause()
        return None


@MobyBot.command(
    pass_context=True,
    description="Sends how many songs are queued to chat.")
async def playlist(ctx, *args):
    """
    Sends how many songs are queued to chat.
    Usage: !playlist
    
    :param ctx: Discord context
    :return: None
    """
    return await MobyBot.say('{0.author.mention} {1} songs in queue.'.format(ctx.message,
                                                                             bot_states.sound_queue.qsize()))

@MobyBot.command(
    pass_context=True,
    description="Restarts the bot.")
async def restart(ctx):
    """
    Exits the Python program and restarts the script.
    Usage: !restart
    
    :param ctx: Context
    :return: None
    """
    author = ctx.message.author
    channel = ctx.message.channel

    print("[Command] ({0}) restart".format(author.name))

    if author.permissions_in(channel).administrator:
        msg = '{0.author.mention} Restarting.'.format(ctx.message)
        await MobyBot.send_message(channel, msg)

        MobyBot.close()
        exit()

    else:
        msg = '{0.author.mention} Insufficient privllages, scrub.'.format(ctx.message)
        return await MobyBot.send_message(channel, msg)


@MobyBot.command(
    pass_context=True,
    description="Resumes the currently paused song.")
async def resume(ctx, *args):
    """
    Resumes the currently paused song.
    Usage: !resume
    A song must be queued for this to work.
    
    :param ctx: Discord context
    :return: None
    """
    if bot_states.player is None:
        return await MobyBot.say('{0.author.mention} Nothing is paused.'.format(ctx.message))
    elif bot_states.player.is_playing():
        return await MobyBot.say('{0.author.mention} Nothing is paused.'.format(ctx.message))
    elif not bot_states.player.is_done() and not bot_states.player.is_playing():
        bot_states.player.resume()
        return await MobyBot.say('{0.author.mention} Resumed playback.'.format(ctx.message))


@MobyBot.command(
    pass_context=True,
    description="Everything after the command is repeated by Moby and the original message is deleted.")
async def say(ctx, *args):
    """
    Everything after the command is repeated by Moby and the original message is deleted.
    Usage: !say Words here are repeated.
    
    :param ctx: Context
    :param args: all text after command
    :return: None
    """

    print("[Command] ({0}) say".format(ctx.message.author.name))

    # create message by concatenating string
    msg = ' '.join(args)
    # delete the original message from the context
    await MobyBot.delete_message(ctx.message)
    # Moby speaks
    return await MobyBot.say(msg)


@MobyBot.command(
    pass_context=True,
    description="Link Moby's source code.")
async def source(ctx):
    """
    Link Moby's source code.
    Usage: !source
    
    :param ctx: Context
    :return: None
    """
    print("[Command] ({0}) source".format(ctx.message.author.name))

    msg = '{0.author.mention} Here is my source code: https://github.com/patthomasrick/moby-bot'.format(ctx.message)
    return await MobyBot.send_message(ctx.message.channel, msg)


@MobyBot.command(
    pass_context=True,
    description="Stops the current song.")
async def stop(ctx):
    """
    Stops the current song.
    Usage: !stop
    A song must be playing.
    
    :param ctx: Discord context
    :return: None
    """
    if bot_states.player is None:
        return await MobyBot.say('{0.author.mention} Nothing is playing.'.format(ctx.message))
    elif not bot_states.player.is_playing() and bot_states.player.is_done():
        return await MobyBot.say('{0.author.mention} Nothing is playing.'.format(ctx.message))
    else:
        bot_states.player.stop()
        return await MobyBot.say('{0.author.mention} Playback stopped.'.format(ctx.message))


@MobyBot.command(
    pass_context=True,
    description="Send Cowan a text!")
async def tellcowan(ctx, *args):
    """
    Send Cowan a text!
    Connects to the AOL.com SMTP server, logs in, formats the email, sends the email to the
    text gateway for Cowan, and Sprint sends Cowan a text containing the email's content.
    Usage: !tellcowan Everything here is sent to Cowan.
    
    :param ctx: Context
    :param args: Everything following the command, which is echoed.
        Should be of the form {word1} {word2} ... {wordn}
    :return: None
    """

    print("[Command] ({0}) tellcowan".format(ctx.message.author.name))

    # create message by concatenating string
    text = ' '.join(args)
    message = MIMEText(text)
    message['From'] = email_address
    message['To'] = cowan_text_gateway

    # init email stuff, connects to the server only when needed
    smtp = aiosmtplib.SMTP(hostname=email_smtp, port=email_port, loop=loop, use_tls=False)
    await smtp.connect()
    await smtp.ehlo()
    await smtp.starttls()
    await smtp.ehlo()
    await smtp.login(email_username, email_password)

    try:
        if len(message) >= 160:
            raise IndexError
        else:
            await smtp.send_message(message)
            await MobyBot.say('{0.author.mention} Text sent.'.format(ctx.message))
    except aiosmtplib.SMTPException:
        await MobyBot.say('{0.author.mention} Failed to send text/email.'.format(ctx.message))
    except IndexError:
        await MobyBot.say('{0.author.mention} That message is too long.'.format(ctx.message))

    smtp.close()


@MobyBot.command(
    pass_context=True,
    description="Sets the volume of the currently playing song. Volume is from 1-100.")
async def volume(ctx, *args):
    """
    Sets the volume of the currently playing song. Volume is from 0-100.
    Usage: !volume (number between 0 and 100)
    :param ctx: Discord context
    :return: None
    """
    if int(args[0]) <= 0 or int(args[0]) > 100:
        return await MobyBot.say('{0.author.mention} Volume must be between 0 and 100.'.format(ctx.message))

    else:
        bot_states.volume = float(args[0]) / 100.0
        return await MobyBot.say('{0.author.mention} Set volume to {1}.'.format(ctx.message, args[0]))


@MobyBot.command(
    pass_context=True,
    description="Plays the YouTube video's sound. Usage: !ytplay link")
async def ytplay(ctx, *args):
    """
    Plays the YouTube video's sound. 
    Usage: !ytplay link
    
    :param ctx: Discord context
    :return: None
    """
    print("[Command] ({0}) ytplay {1}".format(ctx.message.author.name, args[0]))

    # remove playlist info and stuff if present
    yt_url = args[0]
    if "&" in yt_url:
        yt_url = args[0].split("&")[0]

    if ctx.message.author.voice_channel is None:
        return await MobyBot.say('{0.author.mention} You have to be in a Voice Channel.'.format(ctx.message))
    elif bot_states.voice_client is None:
        bot_states.voice_client = await MobyBot.join_voice_channel(ctx.message.author.voice_channel)
    elif ctx.message.author.voice_channel is not bot_states.voice_client.channel:
        bot_states.voice_client = await MobyBot.join_voice_channel(ctx.message.author.voice_channel)

    if bot_states.player is not None:
        if bot_states.player.is_playing():
            bot_states.sound_queue.put(yt_url)
            await MobyBot.delete_message(ctx.message)
            await MobyBot.say('{0.author.mention} Queued - <{1}>.'.format(ctx.message, yt_url))
            return None

    bot_states.player = await bot_states.voice_client.create_ytdl_player(
        url=yt_url,
        ytdl_options=yt_player_opts,
        before_options=yt_player_before_args)
    # delete the original message from the context
    await MobyBot.delete_message(ctx.message)
    await MobyBot.say('{0.author.mention} Now playing - {1.title}.'.format(ctx.message, bot_states.player))
    bot_states.player.volume = bot_states.volume
    bot_states.player.start()

    return None


# here are a bunch of sound clip shortcuts
@MobyBot.command(
    pass_context=True,
    description="Plays the MLG airhorn noise in the user's current voice channel.")
async def airhorn(ctx):
    """
    Plays the MLG airhorn noise in the user's current voice channel.
    Usage: !airhorn
    User must be in a voice channel.
    
    :param ctx: Discord context
    :return: None
    """
    print("[Command] ({0}) airhorn".format(ctx.message.author.name))

    intercept = ctx.message
    intercept.content = "!ytplay https://www.youtube.com/watch?v=N30MkO2KcWc"

    return await MobyBot.process_commands(intercept)


@MobyBot.command(
    pass_context=True,
    description="Plays the Yee noise in the user's current voice channel.")
async def yee(ctx):
    """
    Plays the Yee noise in the user's current voice channel.
    Usage: !yee
    User must be in a voice channel.
    
    :param ctx: Discord context
    :return: None
    """
    print("[Command] ({0}) airhorn".format(ctx.message.author.name))

    intercept = ctx.message
    intercept.content = "!ytplay https://www.youtube.com/watch?v=q6EoRBvdVPQ"

    return await MobyBot.process_commands(intercept)


@MobyBot.command(
    pass_context=True,
    description="Plays the Windows noise in the user's current voice channel.")
async def windows(ctx):
    """
    Plays the Windows noise in the user's current voice channel.
    Usage: !windows
    User must be in a voice channel.
    
    :param ctx: Discord context
    :return: None
    """
    print("[Command] ({0}) airhorn".format(ctx.message.author.name))

    intercept = ctx.message
    intercept.content = "!ytplay https://www.youtube.com/watch?v=6Joyj0dmkug"

    return await MobyBot.process_commands(intercept)


if __name__ == '__main__':
    MobyBot.run(bot_token)
