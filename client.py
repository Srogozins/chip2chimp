#!/usr/bin/env python
import logging
from omegle import OmegleSession
import os
import sys
import urwid

logging.getLogger().setLevel(logging.INFO)

CHATLOG_FILE = "chatlog/chat.log"

palette = [('UserInput', 'default,bold', 'default', 'bold'), ]
prompt = urwid.Edit(('UserInput', ">> "))
output = urwid.Text("")
div = urwid.Divider('#')
pile = urwid.Pile([div, output, div, prompt])

session = None

class Outer(urwid.Filler):
    def keypress(self, size, key):
        if key == '`':
            raise urwid.ExitMainLoop()
        if key != 'enter':
            return super(Outer, self).keypress(size, key)
        self.session.send_message(prompt.edit_text)
        prompt.set_edit_text('')

outer = Outer(pile, valign='bottom')


def output_text(text):
    if type(text) == bytes:
        text = str(text, 'utf-8')
    output.set_text("%s%s%s" % (os.linesep, output.text, text))
    if "Stranger has disconnected" in text:
        raise urwid.ExitMainLoop()

class OmegleClientUI(object):
    def __init__(self):
        self.palette = [('UserInput', 'default,bold', 'default', 'bold'), ]
        self.prompt = urwid.Edit(('UserInput', ">> "))
        self.output = urwid.Text("")
        self.div = urwid.Divider('#')
        self.pile = urwid.Pile([self.div, self.output, self.div, self.prompt])
        self.top = Outer(self.pile, valign='bottom')


def main():
    topics = sys.argv[1:]
    main_loop = urwid.MainLoop(outer, palette, handle_mouse=False)
    cli_chat_output_fd = main_loop.watch_pipe(output_text)
    cli_chat_output = open(cli_chat_output_fd, 'w', 1)
    chatlog_f = open(CHATLOG_FILE, 'a', 1)
    chat_outputs = (cli_chat_output, chatlog_f)

    outer.session = OmegleSession(topics, chat_outputs=chat_outputs)

    main_loop.run()

if __name__ == "__main__":
    main()
