import logging
import asyncio
import aiohttp
import struct
import json
from consts import (
    WS_HOST, WS_PORT, WS_URI,
    WS_HEADER_STRUCT,
    HEADER_LENGTH, MAGIC, VERSION, MAGIC_PARAM,
    HEART_BEAT, JOIN_CHANNEL,
    WS_OP_CONNECT_SUCCESS, WS_OP_HEARTBEAT_REPLY, WS_OP_MESSAGE,
    HEARTBEAT_DELAY,
    API_LIVE_BASE_URL, GET_REAL_ROOM_URI
)
from utils import (
    random_user_id
)

logger = logging.getLogger('bili')
ws_struct = struct.Struct(WS_HEADER_STRUCT)


class BiliLive(object):
    def __init__(self, room_id, user_cookie=None, loop=None,
                 connector=None):
        if not loop:
            loop = asyncio.get_event_loop()

        if not connector:
            connector = aiohttp.TCPConnector(loop=loop)

        self.room_id = room_id
        self.user_cookie = user_cookie
        self.user_id = None
        self.user_login_status = False
        self.session = aiohttp.ClientSession(loop=loop, connector=connector,
                                             cookies=user_cookie)
        self._ws = None
        self._heart_beat_task = None
        self._check_error = None

    async def get_real_room_id(self, room_id):
        real_room_id = room_id
        try:
            res = await self.session.get(
                r'http://{host}:{port}/{uri}'.format(
                    host=API_LIVE_BASE_URL,
                    port=80,
                    uri=GET_REAL_ROOM_URI
                ), params={'id': self.room_id})
            data = await res.json()
            real_room_id = data['data']['room_id']
        except Exception as e:
            logger.exception(e)
        finally:
            return real_room_id

    async def connect(self):
        try:
            self.room_id = await self.get_real_room_id(self.room_id)
            await self.check_user_login_status()
            async with self.session.ws_connect(
                    r'ws://{host}:{port}/{uri}'.format(
                        host=WS_HOST,
                        port=WS_PORT,
                        uri=WS_URI
                    )) as ws:
                self._ws = ws
                await self.send_join_room()
                self._heart_beat_task = asyncio.ensure_future(self.heart_beat())
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        await self.on_binary(msg.data)
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        self.on_close()
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        self.on_error()
        except Exception as e:
            logger.exception(e)

    async def check_user_login_status(self):
        if not self.user_cookie:
            self.user_id = random_user_id()
            return

    async def send_join_room(self):
        await self.send_socket_data(action=JOIN_CHANNEL,
                                    payload=json.dumps({'uid': self.user_id, 'roomid': self.room_id}).replace(' ', ''))

    async def send_socket_data(self, action, payload='',
                               magic=MAGIC, ver=VERSION, param=MAGIC_PARAM):
        try:
            payload = bytearray(payload, 'utf-8')
            packet_length = len(payload) + HEADER_LENGTH
            data = struct.pack(WS_HEADER_STRUCT, packet_length, magic, ver, action, param) + payload
            await self._ws.send_bytes(data)
        except Exception as e:
            logger.exception(e)

    async def heart_beat(self):
        while True:
            try:
                logger.debug("Sending heart beat")
                await self.send_socket_data(action=HEART_BEAT)
                await asyncio.sleep(HEARTBEAT_DELAY)
            except Exception as e:
                logger.exception(e)

    def on_error(self):
        """
        Generally speaking, on_close will be invoked after on_error
        """
        logger.error("on_error is called")

    def on_close(self):
        """
        We need rerun the WebSocket loop in another thread. Because we are
        currently at the end of a WebSocket loop running inside
        self.ws_loop_thread.

        DO NOT join on that thread, that is the current thread
        """
        logger.error("on_close is called")

    async def on_binary(self, binary):
        try:
            while binary:
                packet_length, header_length, a, operation, b = (ws_struct.unpack_from(binary))
                if operation == WS_OP_MESSAGE:
                    self.on_message(binary[header_length:packet_length].decode('utf-8', 'ignore'))
                elif operation == WS_OP_CONNECT_SUCCESS:
                    pass
                elif operation == WS_OP_HEARTBEAT_REPLY:
                    pass
                binary = binary[packet_length:]
        except Exception as e:
            logger.warning("cannot decode message: %s" % e)
            return

    def on_message(self, message):
        try:
            print(json.loads(message))
        except Exception as e:
            pass
