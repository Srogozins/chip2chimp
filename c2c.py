#!/usr/bin/env python3
import logging
import sys

from omegle import OmegleSession
from cleverbot import cleverbot

logging.getLogger().setLevel(logging.DEBUG)

# Hard-coded constants
CHATLOG_FILE = "chatlog/chat.log"


class Chip2ChimpSession(object):
    def __init__(self, topics=(), chatlog=None):
        self.cleverbot = cleverbot.Session()
        self.omegle = OmegleSession(topics)
        self.omegle.register_event_callback('waiting', self._handle_event_waiting)
        self.omegle.register_event_callback('connected', self._handle_event_connected)
        self.omegle.register_event_callback('typing', self._handle_event_typing)
        self.omegle.register_event_callback('stoppedTyping', self._handle_event_typing)
        self.omegle.register_event_callback('gotMessage', self._handle_event_gotMessage)
        self.omegle.register_event_callback('gotMessage', self._handle_event_gotMessage_cleverbot_respond)
        self.omegle.register_event_callback('strangerDisconnected', self._handle_event_strangerDisconnected)

    def _handle_chat_output(self, msg):
        print(msg)

    def _handle_event_waiting(self, event):
        msg = "Waiting for stranger to connect..."
        logging.info(msg)
        self._handle_chat_output(msg)

    def _handle_event_connected(self, event):
        msg = "Stranger has connected."
        logging.info(msg)
        self._handle_chat_output(msg)
        self.connected = True

    def _handle_event_typing(self, event):
        msg = "Stranger is typing"
        logging.info(msg)
        self._handle_chat_output(msg)

    def _handle_event_stoppedTyping(self, event):
        logging.info('Stranger has stopped typing.')

    def _handle_event_gotMessage(self, event):
        text = event[1]
        msg = "Stranger: %s" % text
        logging.info(msg)
        self._handle_chat_output(msg)

    def _handle_event_gotMessage_cleverbot_respond(self, event):
        text = event[1]
        answer = self.cleverbot.Ask(text)
        msg = ("Cleverbot: {}".format(answer))
        self._handle_chat_output(msg)
        logging.info("Sending answer from Cleverbot: {}".format(answer))
        if not self.omegle.send_message(answer):
            self._handle_chat_output("Failed sending chat message.")

    def _handle_event_strangerDisconnected(self, event):
        msg = "Stranger has disconnected"
        logging.info(msg)
        self._handle_chat_output(msg)
        self.omegle.disconnect()

    def run(self):
        self.omegle.run()


def main():
    topics = sys.argv[1:]
    chatlog = open(CHATLOG_FILE, 'a', 1)
    c2c = Chip2ChimpSession(topics=topics, chatlog=chatlog)
    c2c.run()

if __name__ == '__main__':
    main()
