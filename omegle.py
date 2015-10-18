import asyncio
import aiohttp
import logging
from random import choice
import requests

# Logging
logging.basicConfig(filename='omegle.log')
logging.basicConfig(level=logging.DEBUG)

# Header constants
ORIGIN = 'http://www.omegle.com'
ACCEPT_ENCODING = 'gzip, deflate'
ACCEPT_LANGUAGE = 'en   -GB,en-US;q=0.8,en;q=0.6'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
CONTENT_TYPE = 'application/x-www-form-urlencoded; charset=UTF-8'
ACCEPT = 'application/json'
SEND_ACCEPT = 'text/javascript, text/html, application/xml, text/xml, */*'
REFERER = 'http://www.omegle.com'
CONNECTION = 'keep-alive'
HEADERS = {'Origin': ORIGIN,
           'Accept-Encoding': ACCEPT_ENCODING,
           'Accept-Language': ACCEPT_LANGUAGE,
           'User-Agent': USER_AGENT,
           'Content-type': CONTENT_TYPE,
           'Accept': ACCEPT,
           'Referer': REFERER,
           'Connection': CONNECTION}

SEND_HEADERS = {'Origin': ORIGIN,
                'Accept-Encoding': ACCEPT_ENCODING,
                'Accept-Language': ACCEPT_LANGUAGE,
                'User-Agent': USER_AGENT,
                'Content-type': CONTENT_TYPE,
                'Accept': SEND_ACCEPT,
                'Referer': REFERER,
                'Connection': CONNECTION}

OMEGLE_URL_BASE = 'http://front1.omegle.com'

LANGUAGE = 'en'

HANDLED_EVENTS = ['waiting',
                  'connected',
                  'typing',
                  'stoppedTyping',
                  'gotMessage',
                  'strangerDisconnected',
                  'statusInfo',
                  'identDigests']


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


async def events_request(clientID):
    """Request for events

    Args:
        clientID (str): ID retrieved from start request
    Returns:
    """
    logging.info("Requesting events")
    url = OMEGLE_URL_BASE + '/events'
    payload = {'id': clientID}
    resp = await aiohttp.request('POST', url, data=payload, headers=HEADERS)
    return resp


def send_request(clientID, msg):
    """Send chat message

    Args:
        clientID (str): ID retrieved from start request
    Returns:
        Response object
    """
    logging.info("Sending message: {}".format(msg))
    url = OMEGLE_URL_BASE + '/send'
    payload = {'id': clientID,
               'msg': msg}
    r = requests.post(url, data=payload, headers=HEADERS)
    return r


class EventHandler:
    """Generic class for mapping event types to callbacks that handle them"""
    def __init__(self, event_types=[]):
        self._event_handlers = {et: [] for et in event_types}

    def attach(self, event_type, callback):
        if event_type not in self._event_handlers:
            raise Exception("Unhandled event type: {}".format(event_type))
        if callback in self._event_handlers[event_type]:
                raise Exception("Callback already registered")
        self._event_handlers[event_type].append(callback)

    def detach(self,  event_type, callback):
        if event_type not in self._event_handlers:
            raise Exception("Unhandled event type: {}".format(event_type))
        try:
            self._event_handlers[event_type].remove(callback)
        except ValueError:
            raise Exception("Callback not registered")

    def handle(self, event):
        event_type = event[0]
        if event_type not in self._event_handlers:
            raise Exception("Unhandled event type: {}".format(event_type))
        for callback in self._event_handlers[event_type]:
            callback(event)


# TODO: context manager?
class OmegleSession:
    """ Class for establishing an Omegle chat session and binding callbacks to chat events"""

    def __init__(self, topics=()):
        self._topics = topics
        self._event_handler = EventHandler(HANDLED_EVENTS)

        self._connected = False
        self.is_active = False
        self._event_queue = asyncio.Queue()

    def register_event_callback(self, event_type, callback):
        self._event_handler.attach(event_type, callback)

    def deregister_event_callback(self, event_type, callback):
        self._event_handler.dettach(event_type, callback)

    def run(self):
        self.is_active = True
        if self._connect():
            self._connected = True
            loop = asyncio.get_event_loop()
            loop.set_debug(True)
            logging.info('Starting main event loop')
            try:
                loop.run_until_complete(asyncio.gather(self._gather_events(),
                                                       self._process_events()))
            except aiohttp.errors.ClientResponseError:
                logging.warning("ClientResponseError raised")
                self.disconnect()
            finally:
                loop.close()
            logging.info('Main event loop closed')
            self.is_active = False

    async def _gather_events(self):
        logging.info('Starng event gathering')
        while self._connected:
            resp = await events_request(self._clientID)
            logging.info('Got events response, extracting from json.')
            logging.debug(resp)
            j = await resp.json()
            if not j:
                logging.info('Got no events this time.')
                continue
            logging.info('Got events, putting in queue.')
            logging.debug(j)
            for e in j:
                await self._event_queue.put(e)
        logging.info('Ending event gathering')

    async def _process_events(self):
        logging.info('Starting event processing')
        while self._connected:
            logging.info("Attempting to retrieve event from queue.")
            await asyncio.sleep(5)
            event = await self._event_queue.get()
            logging.info("Event retrieved.")
            logging.debug(event)
            # Handle event
            self._event_handler.handle(event)
        logging.info('Ending event processing')

    def disconnect(self):
        logging.info('Disconnecting')
        self._connected = False

    def _connect(self):
        msg = "Connecting"
        logging.info(msg)
        r = start_request(self._topics)
        if r:
            msg = "Connected"
            logging.info(msg)
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
            return True
        else:
            msg = ("Failed sending chat message.")
            logging.warning(msg)
            return False
