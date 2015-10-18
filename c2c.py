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
        self._chatlog = chatlog
        self._cleverbot = cleverbot.Session()
        self._omegle = OmegleSession(topics)
        self._omegle.register_event_callback('waiting', self._handle_event_waiting)
        self._omegle.register_event_callback('connected', self._handle_event_connected)
        self._omegle.register_event_callback('typing', self._handle_event_typing)
        self._omegle.register_event_callback('stoppedTyping', self._handle_event_typing)
        self._omegle.register_event_callback('gotMessage', self._handle_event_gotMessage)
        self._omegle.register_event_callback('gotMessage', self._handle_event_gotMessage_cleverbot_respond)
        self._omegle.register_event_callback('strangerDisconnected', self._handle_event_strangerDisconnected)

    # TODO: Move obvious stuff to default event handlers
    def _handle_chat_output(self, msg):
        print(msg)
        if self._chatlog:
            print(msg, file=self._chatlog)

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
        answer = self._cleverbot.Ask(text)
        msg = ("Cleverbot: {}".format(answer))
        self._handle_chat_output(msg)
        logging.info("Sending answer from Cleverbot: {}".format(answer))
        if not self._omegle.send_message(answer):
            self._handle_chat_output("Failed sending chat message.")

    def _handle_event_strangerDisconnected(self, event):
        msg = "Stranger has disconnected"
        logging.info(msg)
        self._handle_chat_output(msg)
        self._omegle.disconnect()

    def run(self):
        self._omegle.run()


def main():
    topics = sys.argv[1:]
    chatlog = open(CHATLOG_FILE, 'a', 1)
    c2c = Chip2ChimpSession(topics=topics, chatlog=chatlog)
    c2c.run()
    chatlog.close()

if __name__ == '__main__':
    main()
