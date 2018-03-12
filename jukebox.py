"""
Author: Patrick Thomas

Controls sound playback of Moby.
"""

import asyncio

import discord


async def jukebox(moby_bot, bot_states, yt_player_opts, yt_player_before_args):
    """
    A simple playlist manager function, designed to run
    concurrently and constantly.
    :return: None
    """

    # don't start until the bot is logged in
    await moby_bot.wait_until_ready()

    # only run while the bot is active
    while not moby_bot.is_closed:
        await asyncio.sleep(2)  # task runs every n seconds

        if bot_states.sound_queue.empty():
            pass  # do nothing if there are no songs in the queue

        elif bot_states.sound_queue.not_empty():
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
                    await moby_bot.say('Now playing - {0.title}.'.format(bot_states.player))
                    await moby_bot.change_presence(game=discord.Game(name=bot_states.player.title))

        else:  # otherwise just say that he's on brainpop
            await moby_bot.change_presence(game=discord.Game(name='Brainpop.com'))
