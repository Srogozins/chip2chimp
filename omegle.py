import http.client
import logging
from random import choice
import requests
from threading import Thread

# Logging
# http.client.HTTPConnection.debuglevel = 1
logging.basicConfig(filename='omegle.log')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger().setLevel(logging.INFO)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

# Header constants
ORIGIN = 'http://www.omegle.com'
ACCEPT_ENCODING = 'gzip, deflate'
ACCEPT_LANGUAGE = 'en-GB,en-US;q=0.8,en;q=0.6'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
CONTENT_TYPE = 'application/x-www-form-urlencoded; charset=UTF-8'
ACCEPT = 'application/json'
SEND_ACCEPT = 'text/javascript, text/html, application/xml, text/xml, */*'
REFERER = 'http://www.omegle.com'
CONNECTION = 'keep-alive'
CONTENT_LENGTH = '0'
HEADERS = {'Origin': ORIGIN,
           'Accept-Encoding': ACCEPT_ENCODING,
           'Accept-Language': ACCEPT_LANGUAGE,
           'User-Agent': USER_AGENT,
           'Content-type': CONTENT_TYPE,
           'Accept': ACCEPT,
           'Referer': REFERER,
           'Connection': CONNECTION,
           'Content-Length': CONTENT_LENGTH, }

SEND_HEADERS = {'Origin': ORIGIN,
                'Accept-Encoding': ACCEPT_ENCODING,
                'Accept-Language': ACCEPT_LANGUAGE,
                'User-Agent': USER_AGENT,
                'Content-type': CONTENT_TYPE,
                'Accept': SEND_ACCEPT,
                'Referer': REFERER,
                'Connection': CONNECTION,
                'Content-Length': CONTENT_LENGTH, }

OMEGLE_URL_BASE = 'http://front1.omegle.com'

LANGUAGE = 'en'


def randID():
    charpool = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return ''.join(charpool[i] for i in [choice(range(0, 32)) for i in range(0, 8)])


# Requests
def start_request(topics=[]):
    """Request to start search for stranger to talk to

    Args:
        topics (list): list of common topics, defaults to []
    Returns:
        Response object
    """
    randid = randID()

    url = OMEGLE_URL_BASE + '/start'
    payload = {'rcs': 1,
               'firstevents': 1,
               'spid': "",
               'randid': randid,
               'topics': str(topics),
               'lang': LANGUAGE, }
    r = requests.post(url, params=payload, headers=HEADERS)
    return r


def events_request(clientID):
    """Request for events

    Args:
        clientID (str): ID retrieved from start request
    Returns:
        Response object
    """
    url = OMEGLE_URL_BASE + '/events'
    payload = {'id': clientID}
    r = requests.post(url, data=payload, headers=HEADERS)
    return r


def send_request(clientID, msg):
    """Send chat message

    Args:
        clientID (str): ID retrieved from start request
    Returns:
        Response object
    """
    url = OMEGLE_URL_BASE + '/send'
    payload = {'id': clientID,
               'msg': msg}
    r = requests.post(url, data=payload, headers=HEADERS)
    return r


# TODO: context manager
class OmegleSession:

    def __init__(self, topics=()):
        self._topics = topics
        self._chat_output_callbacks = []
        self._stranger_output_callbacks = []     # where only clean Stranger text goes
        self._connected = False

        # TODO: Make variables used to check if session should be terminated thread-safe
        self._is_stranger_bot = False
        self._has_stranger_typed = False
        self._stranger_disconnected = False
        self.is_active = False

        self._event_handlers = {'waiting': self._handle_event_waiting,
                                'connected': self._handle_event_connected,
                                'typing': self._handle_event_typing,
                                'stoppedTyping': self._handle_event_stoppedTyping,
                                'gotMessage': self._handle_event_gotMessage,
                                'strangerDisconnected': self._handle_event_strangerDisconnected}
        self.event_list = []

    def register_output_callback(self, callback, stranger_output_only=False):
        if stranger_output_only:
            self._stranger_output_callbacks.append(callback)
        else:
            self._chat_output_callbacks.append(callback)

    def run(self):
        self.is_active = True
        if self._connect():
            self._t_event_handling = Thread(target=self._process_events_loop, daemon=True)
            self._t_event_handling.start()

    def _connect(self):
        msg = "Connecting"
        logging.info(msg)
        self._handle_chat_output(msg)
        r = start_request(self._topics)
        if r:
            msg = "Connected"
            logging.info(msg)
            self._handle_chat_output(msg)
            self._clientID = r.json()['clientID']
            return True
        else:
            msg = "Could not connect"
            logging.warning(msg)
            return False

    def send_message(self, chat_msg):
        # TODO: typing
        resp = send_request(self._clientID, chat_msg)
        if resp:
            msg = ("You: %s" % chat_msg)
            logging.info(msg)
        else:
            msg = ("Failed sending chat message.")
            logging.warning(msg)
        self._handle_chat_output(msg)

    def _time_to_stop(self):
        return self._is_stranger_bot or self._stranger_disconnected

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
        self._has_stranger_typed = True

    def _handle_event_stoppedTyping(self, event):
        logging.info('Stranger has stopped typing.')

    def _handle_event_gotMessage(self, event):
        text = event[1]
        self._handle_stranger_output(text)
        msg = "Stranger: %s" % event[1]
        logging.info(msg)
        self._handle_chat_output(msg)
        # if not self._has_stranger_typed:
        #     msg = "Stranger pasted a message, stranger is likely a bot!"
        #     logging.warning(msg)
        #     self._handle_chat_output(msg)

    def _handle_event_strangerDisconnected(self, event):
        msg = "Stranger has disconnected"
        logging.info(msg)
        self._handle_chat_output(msg)
        self._stranger_disconnected = True

    def _process_events_loop(self):
        logging.info('Starting event processing loop')
        while not self._time_to_stop():
            events = self._get_events()
            self.event_list.extend(events)

            # Handle events
            for e in events:
                event_type = e[0]
                if event_type not in self._event_handlers:
                    logging.warning('Unhandled event type: %s' % event_type)
                else:
                    self._event_handlers[event_type](e)
        self.is_active = False

    def _get_events(self):
        logging.info('Requesting events')
        r = events_request(self._clientID)
        events = r.json()
        logging.info('Received %i events' % len(events))
        logging.debug('Received events: %s' % events)
        return events

    def _handle_chat_output(self, output):
        for cb in self._chat_output_callbacks:
            cb(output)

    def _handle_stranger_output(self, output):
        for cb in self._stranger_output_callbacks:
            cb(output)
