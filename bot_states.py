"""
Author: Patrick Thomas

To contain the class BotStates, which helps with keeping track of internal data of the Discord Bot.
"""

from queue import Queue


class BotStates:
    def __init__(self):
        # states that the bot can be in
        self.annoying_mode = False  # responding to all messages with !chat?
        self.voice_client = None  # current voice client for sounds
        self.player = None  # current sound player
        self.volume = 0.8  # volume of sound player
        self.sound_queue = Queue()  # songs queued

        self.locked = False  # admin only mode
