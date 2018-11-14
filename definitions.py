# -*- coding: utf-8 -*-
__author__ = 'gzp'

import collections

Danmaku = collections.namedtuple(
    'Danmaku',
    ['danmu_header', 'content', 'user_info', 'user_badge', 'user_level', 'user_title', 'user_is_vip', 'user_is_svip',
     'name_color']
)
