import asyncio
import json
from email.mime.text import MIMEText
from random import choice

import aiosmtplib
import discord
from chatterbot import ChatBot
from discord.ext.commands import Bot

from settings import read_settings

# Discord bot initialization
client = discord.Client()
description = '''Moby serves to protect, as well as be the host of the hit online series, the
Adventures of Tim and Moby!'''
MobyBot = Bot(command_prefix='!', description=description)

# Load settings file
options = read_settings('settings.txt')

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

# init chatterbot
chatbot = ChatBot(chat_bot_name, trainer='chatterbot.trainers.ChatterBotCorpusTrainer')
chatbot.train("chatterbot.corpus.english")

loop = asyncio.get_event_loop()


class AnnoyingModeState:
    def __init__(self):
        self.state = False


annoying_mode_state = AnnoyingModeState()


@MobyBot.event
async def on_ready():
    """
    Runs when the bot joins the server and is ready to respond to requests.
    Currently, Bonzi just outputs to the console that he is ready.
    :return: None
    """
    print('Connected!')
    print('Username: ' + MobyBot.user.name)
    print('ID: ' + MobyBot.user.id)

    await client.login(client_email, client_password)


@MobyBot.event
async def on_message(message):
    """
    Does stuff on message sent
    :param message: the message object itself
    :return: none
    """

    # do a command
    if message.content.startswith('!'):
        return await MobyBot.process_commands(message)

    else:
        # # cowanify cowan's messages
        # if message.author.name == "cowrone":
        #     print("[Trigger] Found message from {0}".format(message.author.name))
        #     # get the emoji
        #     emojis = MobyBot.get_all_emojis()
        #     for e in emojis:
        #         if e.name == "cowan":
        #             await MobyBot.add_reaction(message, e)
        #             break
        #
        # # patrickfy patrick's messages
        # elif message.author.name == "Sillyurs":
        #     print("[Trigger] Found message from {0}".format(message.author.name))
        #     # get the emoji
        #     emojis = MobyBot.get_all_emojis()
        #     for e in emojis:
        #         if e.name == "bonzi":
        #             await MobyBot.add_reaction(message, e)
        #             break

        # ensure bot doesn't respond to self in annoyingmode
        if annoying_mode_state.state and message.author.name != "Moby":
            # get response
            response = chatbot.get_response(message.content)
            print("[Command] ({0}) chat \"{1}\"->\"{2}\"".format(message.author.name,
                                                                 message.content,
                                                                 response))
            MobyBot.send_message(message.channel, response)


@MobyBot.command(
    pass_context=True,
    description="Toggles whether or not Moby will reply to everything in the channel.")
async def annoyingmode(ctx):
    """
    Toggles whether or not Moby will reply to everything in the channel.
    :param ctx: Discord context
    :return: None
    """
    print("[Command] ({0}) annoyingmode".format(ctx.message.author.name))

    if annoying_mode_state.state:
        annoying_mode_state.state = False
        return MobyBot.send_message(ctx.message.channel, "Annoying mode off.")

    else:
        annoying_mode_state.state = True
        return MobyBot.send_message(ctx.message.channel, "Annoying mode on.")


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
    description="Choose between multiple choices separated by spaces.")
async def choose(ctx, *choices: str):
    """
    Choose between multiple choices
    :param ctx: Discord context
    :param choices: words following the command
    :return: None
    """
    print("[Command] ({0}) choices {1}".format(ctx.message.author.name, choices))

    return await MobyBot.say(choice(choices))


@MobyBot.command(
    pass_context=True,
    description="Send an email from Moby. Usage: !email email@email.com message")
async def email(ctx, *args):
    """
    Send an email from Moby. Usage: !email email@email.com message
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
    description="Say hello back to people.")
async def hello(ctx):
    """
    Say hello back to people.
    :param ctx: Context
    :return: None
    """
    print("[Command] ({0}) hello".format(ctx.message.author.name))

    msg = 'Hello {0.author.mention}'.format(ctx.message)
    return await MobyBot.send_message(ctx.message.channel, msg)


@MobyBot.command(
    pass_context=True,
    description="Tell a random joke from the big list.")
async def joke(ctx):
    """
    Tell a random joke from the big list.
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
    description="Moby repeats the message word for word and deletes the original command.")
async def say(ctx, *args):
    """
    Moby repeats the message word for word and deletes the original command.
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
    description="Send Cowan a text!")
async def tellcowan(ctx, *args):
    """
    Send Cowan a text!
    Connects to the AOL.com SMTP server, logs in, formats the email, sends the email to the
    text gateway for Cowan, and Sprint sends Cowan a text containing the email's content.
    :param ctx: Context
    :param args: Everything following the command, which is echoed back to the chat.
        Should be of the form {email} {word1} {word2} ... {wordn}
    :return: None
    """

    print("[Command] ({0}) tellcowan".format(ctx.message.author.name))

    # init email stuff, connects to the server only when needed
    smtp = aiosmtplib.SMTP(hostname=email_smtp, port=email_port, loop=loop, use_tls=False)
    await smtp.connect()
    await smtp.starttls()
    await smtp.login(email_username, email_password)

    # create message by concatenating string
    text = ' '.join(args)
    message = MIMEText(text)
    message['From'] = email_address
    message['To'] = cowan_text_gateway

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


if __name__ == '__main__':
    MobyBot.run(bot_token)
