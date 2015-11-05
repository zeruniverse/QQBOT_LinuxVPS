# -*- coding:utf-8 -*-
import logging
import random
import math
import PluginMixin

__author__ = 'sweet'

STATUS_START = 0  # 开始阶段
STATUS_READY = 10  # 准备阶段
STATUS_READY_COMPLETE = 20  # 准备阶段完成
STATUS_SPEAK = 20  # 发言阶段
STATUS_VOTE = 30  # 投票阶段
STATUS_END = 99  # 结束阶段


class playerInfo(object):
    key = ''  # 用户唯一标示，外部维护
    name = ''


class shuishiwodi(object):
    """
    谁是卧底 5人
    """
    status = STATUS_START
    _output = None
    _playcount = 0
    _playerList = []

    def __init__(self, output, playercount):
        self._output = output
        self._playcount = playercount
        pass

    def _id2playerInfo(self, id):
        """
        将编号转换为玩家信息
        :param id: 玩家编号
        :return:playerInfo
        """
        if not isinstance(id, (int, long)):
            raise TypeError()
        if id > 0 and id <= len(self._playerList):
            return self._playerList[id - 1]

    def ready(self):
        if self.status >= STATUS_READY:
            logging.error(u"状态错误，当前状态 %s ，调用方法ready()" % self.status)
            return
        self.status = STATUS_READY
        self._playerList = []
        self._output.info(u"玩游戏啦：谁是卧底 %d 人局，想玩的快快加入~" % self._playcount)
        pass

    def addplayer(self, playerInfo):
        self._playerList.append(playerInfo)
        self._output.info(u"%s 加入游戏，当前人数 %d/%d" % (playerInfo.name, len(self._playerList), self._playcount))
        pass

    def start(self):
        strPlayerList = '\n\t'.join(["[%d]:%s" % (i + 1, p.name) for (i, p) in enumerate(self._playerList)])
        self._output.info((u"游戏开始，本局游戏共 %d 人：\n\t" % self._playcount) + strPlayerList)
        i = int((random.random() * len(self._playerList))) + 1
        playerInfo = self._id2playerInfo(i)
        self._output.info(u"请从%d号玩家[%s]开始，依次发言。" % (i, playerInfo.name))
        pass

    def speak(self):
        pass

    def vote(self):
        pass

    def exit(self):
        self._output.info(u"游戏结束")
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    g = shuishiwodi(logging, 2)
    g.ready()

    p1 = playerInfo()
    p1.name = 'sweet'
    g.addplayer(p1)

    p2 = playerInfo()
    p2.name = 'winnie'
    g.addplayer(p2)

    g.start()
    pass
