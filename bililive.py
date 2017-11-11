import logging
import asyncio
import aiohttp
import consts

LOGGER = logging.getLogger('bili')


class BiliLive(object):
    def __init__(self, room_id, user_cookie=None, loop=None,
                 connector=None):
        if not loop:
            loop = asyncio.get_event_loop()

        if not connector:
            connector = aiohttp.TCPConnector(loop=loop)

        self.room_id = room_id,
        self.user_cookie = user_cookie
        self.user_id = None
        self.user_login_status = False
        self.session = aiohttp.ClientSession(loop=loop, connector=connector,
                                             cookies=user_cookie)
        self._ws = None
        self._heart_beat_task = None
        self._check_error = None

    async def connect(self):
        async with self.session.ws_connect(
                r"ws://{host}:{port}/{uri}".format(
                    host=consts.WS_HOST,
                    port=consts.WS_PORT,
                    uri=consts.WS_URI
                )) as ws:
            self._ws = ws
            await self.send_join_room()
            self._heart_beat_task = asyncio.ensure_future(self.heart_beat())
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    self.on_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    self.on_close()
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.on_error()

    async def check_user_login_status(self):
        if not self.user_cookie:
            pass

    async def send_join_room(self):
        pass

    async def heart_beat(self):
        while True:
            LOGGER.debug("Sending heart beat")
            await self.ws.send_bytes('')
            await asyncio.sleep(30)

    def on_error(self):
        """
        Generally speaking, on_close will be invoked after on_error
        """
        LOGGER.error("on_error is called")

    def on_close(self):
        """
        We need rerun the WebSocket loop in another thread. Because we are
        currently at the end of a WebSocket loop running inside
        self.ws_loop_thread.

        DO NOT join on that thread, that is the current thread
        """
        LOGGER.error("on_close is called")

    def on_message(self, message):
        # TODO: force full update after certain amount of time
        try:
            print(message)
            # message_header = MessageHeader._make(
            #     message_header_struct.unpack_from(message)
            # )
            # if message_header.opcode == 3:
            #     LOGGER.debug("received online message")
            # elif message_header.opcode == 5:
            #     LOGGER.debug("received %d bytes message data" %
            #                  len(message))
            #     self.process_message(message)
            # elif message_header.opcode == 8:
            #     LOGGER.debug("received heart beat request")
            # else:
            #     LOGGER.warning("received data with unknown opcode %d" %
            #                    message_header.opcode)
        except Exception as e:
            LOGGER.warning("cannot decode message: %s" % e)
            return

    def process_message(self, message):
        update_list = []
        offset = 0
        while offset < len(message):
            try:
                message_header = MessageHeader._make(
                    message_header_struct.unpack_from(message, offset)
                )
                data = message[offset + message_header.start_offset:offset +
                                                                    message_header.end_offset]
                message_object = json.loads(data)

                cmd = message_object['cmd']
                if cmd == "DRAW_UPDATE":
                    x = message_object['data']['x_max']
                    y = message_object['data']['y_max']
                    color_code = message_object['data']['color']
                    update_list.append([x, y, color_code])

                    LOGGER.debug(
                        "cmd: %s, update (%d, %d) with color %s" %
                        (cmd, x, y, color_code))
                else:
                    LOGGER.debug("Other message: %s" %
                                 (data))

                offset += message_header.end_offset

            except Exception as err:
                LOGGER.error("Error message (offset: %d): %s, err: %s" %
                             (offset, message, err))
                break

        # finally update the pixels in critical section
        start_time = time.clock()
        for x, y, color_code in update_list:
            rgb = CODE_RGB_TABLE[color_code]
            self.set_image_pixel(x, y, rgb)
            # ignore when guard_region is not used
            if self.guard_region is None:
                continue
            # check guard region
            if (x, y) in self.guard_region:
                desired_color_code = self.guard_region[(x, y)]
                if desired_color_code != color_code:
                    LOGGER.info("(%d, %d) %s triggers the guard region",
                                x, y, color_code)

                    self.task_queue.put_nowait(
                        (self.get_task_priority(x, y),
                         x,
                         y,
                         desired_color_code)
                    )

        LOGGER.debug("process_message update pixels in %.6f" %
                     (time.clock() - start_time))
