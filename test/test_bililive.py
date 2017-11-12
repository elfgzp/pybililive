import logging.config
import asyncio
from bililive import BiliLive

logging.config.fileConfig("../logger.conf")

if __name__ == '__main__':
    live = BiliLive(388)
    asyncio.ensure_future(live.connect())
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    try:
        loop.run_forever()
    except:
        loop.close()
