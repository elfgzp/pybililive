import logging.config
import asyncio
from bililive import BiliLive
from handler import (
    danmmu_msg, send_gift
)

logging.config.fileConfig("../logger.conf")

if __name__ == '__main__':
    cmd_func = {
        'DANMU_MSG': danmmu_msg,  # 接收到弹幕执行的函数
        'SEND_GIFT': send_gift  # 接收到礼物执行的函数
    }
    live = BiliLive(388, cmd_func_dict=cmd_func)
    asyncio.ensure_future(live.connect())
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    try:
        loop.run_forever()
    except:
        loop.close()
