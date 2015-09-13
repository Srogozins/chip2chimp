#!/usr/bin/env python3
import logging
from time import sleep

from omegle import OmegleSession
from cleverbot import cleverbot

logging.getLogger().setLevel(logging.INFO)

# Hard-coded constants
CHATLOG_FILE = "chatlog/chat.log"


class Chip2ChimpSession(object):
    def __init__(self, chatlog):
        self.cleverbot = cleverbot.Session()
        self.omegle = OmegleSession()
        self.omegle.register_output_callback(lambda o: print(o, file=chatlog))
        self.omegle.register_output_callback(self._stranger_output_callback, True)
        self.stranger_answers = []

    def _stranger_output_callback(self, output):
        self.stranger_answers.append(output)

    def run(self):
        self.omegle.run()
        while self.omegle.is_active:
            if len(self.stranger_answers):
                cleverbot_answer = self.cleverbot.Ask(self.stranger_answers.pop())
                self.omegle.send_message(cleverbot_answer)


def main():
    # topics = sys.argv[1:]
    chatlog = open(CHATLOG_FILE, 'a', 1)
    c2c = Chip2ChimpSession(chatlog=chatlog)
    c2c.run()

if __name__ == '__main__':
    main()
