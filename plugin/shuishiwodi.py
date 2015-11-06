# -*- coding:utf-8 -*-

import logging
import random
import re
import time

__author__ = 'sweet'


class PlayerInfo(object):
    def __init__(self):
        self.uin = ''  # 用户唯一标示
        self.id = 0  # 用户编号
        self.name = ''  # 用户昵称
        self.isUndercover = False  # 是否卧底
        self.word = ''  # 抽到的词语
        self.isOut = False  # 是否出局


class MsgDto(object):
    __slots__ = ('poll_type', 'from_uin', 'msg_id', 'msg_id2', 'msg_type', 'reply_ip', 'to_uin', 'raw_content')

    def __init__(self):
        self.from_uin = ''
        self.to_uin = ''
        self.raw_content = ''

    pass


class StatusHandler(object):
    def __init__(self):
        self.status = 'undefined'

    def handle(self, game, msgDto):
        return False  # 退出


class StartStatus(StatusHandler):
    """
    <初始化阶段>
    """

    def __init__(self):
        super(StatusHandler, self).__init__()
        self.status = 'StartStatus'

    def handle(self, game, msgDto):
        playCount = 5
        undercoverCount = 1
        game.writePublic(u"玩游戏啦：谁是卧底 %d 人局，想玩的快快加入~(输入 我要参加，加入游戏)" % playCount)
        game.statusHandle = ReadyStatus(playCount, undercoverCount)
        return True


class ReadyStatus(StatusHandler):
    """
    <准备阶段>
    公告游戏人数
    允许玩家加入游戏
    """
    _playCount = 0
    _undercoverCount = 0

    def __init__(self, playCount, undercoverCount=1):
        super(StatusHandler, self).__init__()
        self.status = 'ReadyStatus'
        self._playCount = playCount
        self._undercoverCount = undercoverCount

    def handle(self, game, msgDto):
        matchSuccess = re.match(r'^\s*我要参加\s*$', msgDto.raw_content)
        if not matchSuccess:
            return False
        playerInfo = PlayerInfo()
        playerInfo.uin = msgDto.from_uin
        playerInfo.name = msgDto.from_uin
        game.addPlayer(playerInfo)
        game.writePublic(u"%s 加入游戏，当前人数 %d/%d" % (playerInfo.name, len(game.playerList), self._playCount))
        if len(game.playerList) >= self._playCount:
            game.statusHandle = AssignRolesStatus(self._undercoverCount)
            return True
        return False


class AssignRolesStatus(StatusHandler):
    """
    <分配角色阶段>
    初始化用户身份信息
    """
    _undercoverCount = 0

    def __init__(self, undercoverCount=1):
        """
        :param undercoverCount: 卧底人数
        :return:
        """
        super(StatusHandler, self).__init__()
        self.status = 'AssignRolesStatus'
        self._undercoverCount = undercoverCount

    def handle(self, game, msgDto):
        maxUndercover = len(game.playerList) // 3
        self._undercoverCount = min(maxUndercover, self._undercoverCount)
        # 获取卧底词
        normalWord, specialWord = self.extractWords()
        # 分配卧底身份
        for x in game.playerList:
            x.isUndercover = False
            x.word = normalWord
        while len(filter(lambda x: x.isUndercover, game.playerList)) < self._undercoverCount:
            i = random.randint(0, len(game.playerList) - 1)
            game.playerList[i].isUndercover = True
            game.playerList[i].word = specialWord
        # 游戏信息
        playerNames = ','.join([x.name for x in game.playerList])
        game.writePublic(u"[%s]本次游戏共 %d 人，卧底 %d 人。\n玩家列表：%s" % (
            game.gameId, len(game.playerList), self._undercoverCount, playerNames))
        # 私聊玩家，通知词语
        for x in game.playerList:
            game.writePrivate(x.uin, u'谁是卧底，您本局[%s]的词语是：%s' % (game.gameId, x.word))
        # 进入发言阶段
        game.statusHandle = SpeechStatus()
        return True

    def extractWords(self):
        """
        抽取平民词与卧底词
        :return:
        """
        return '1', '2'
        pass


class SpeechStatus(StatusHandler):
    """
    <发言阶段>
    玩家依次发言
    """

    def __init__(self, ):
        super(StatusHandler, self).__init__()
        self.status = 'SpeechStatus'
        self._history = {}
        self._first = True
        self._playerSet = set()

    def handle(self, game, msgDto):
        if self._first:
            self._first = False
            lst = [x for x in game.playerList if not x.isOut]
            self._playerSet = set([x.uin for x in lst])
            i = random.randint(0, len(lst) - 1)
            playerInfo = lst[i]
            game.writePublic(u"发言阶段，请从%d号玩家[%s]开始，依次发言。" % (playerInfo.id, playerInfo.name))
        uin = msgDto.from_uin
        content = msgDto.raw_content
        if not uin in self._playerSet:
            return False
        if not uin in self._history:
            self._history[uin] = content
        # 发言结束，进入投票阶段
        if len(self._history) >= len(self._playerSet):
            # lst = [('%s:') for key,value in self._history]
            # playerReplys = '\n'.join()
            # game.writePublic(u"发言结束：\n")
            game.statusHandle = VoteStatus()
            return True
        return False


class VoteStatus(StatusHandler):
    """
    <投票阶段>
    玩家投出代表自己的一票
    """

    def __init__(self, ):
        super(StatusHandler, self).__init__()
        self.status = 'VoteStatus'
        self._history = {}
        self._first = True

    def handle(self, game, msgDto):
        if self._first:
            lst = [('%s: %s' % (x.id, x.name)) for x in game.playerList if not x.isOut]
            self._playerSet = set([x.uin for x in game.playerList if not x.isOut])
            playerNames = '\n'.join(lst)
            game.writePublic(u"投票开始，请投卧底。\n" + playerNames)
        uin = msgDto.from_uin
        content = msgDto.raw_content
        if not uin in self._playerSet:
            return False
        if not uin in self._history:
            try:
                self._history[uin] = int(content)
            except:
                pass
        # 投票结束
        if len(self._history) >= len(self._playerSet):
            pass
        pass

    def verdict(self):
        pass


class EndStatus(StatusHandler):
    """
    <结束阶段>
    公布游戏结果
    """

    def handle(self, game, msgDto):
        pass


class Game(object):
    def __init__(self, statusHandle, output):
        self.statusHandle = statusHandle
        self.gameId = str(int(time.time()))[-5:]
        self._output = output
        self._playerList = []

    @property
    def playerList(self):
        return self._playerList

    def writePublic(self, msg):
        self._output.info(msg)
        pass

    def writePrivate(self, uid, msg):
        self._output.warn('%s:%s' % (uid, msg))
        pass

    def addPlayer(self, playerInfo):
        playerInfo.id = len(self.playerList) + 1
        self.playerList.append(playerInfo)

    def run(self, msgDto):
        while self.statusHandle.handle(self, msgDto):
            pass


# ===========================================================================================


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    status = StartStatus()
    game = Game(status, logging)
    game.run(MsgDto())

    game.run(MsgDto())
    msgDto1 = MsgDto()
    msgDto1.from_uin = '1'
    msgDto1.raw_content = '我要参加'
    game.run(msgDto1)
    msgDto2 = MsgDto()
    msgDto2.from_uin = '2'
    msgDto2.raw_content = '我要参加'
    game.run(msgDto2)
    msgDto3 = MsgDto()
    msgDto3.from_uin = '3'
    msgDto3.raw_content = '我要参加'
    game.run(msgDto3)
    msgDto4 = MsgDto()
    msgDto4.from_uin = '4'
    msgDto4.raw_content = '我要参加'
    game.run(msgDto4)
    msgDto5 = MsgDto()
    msgDto5.from_uin = '5'
    msgDto5.raw_content = '我要参加'
    game.run(msgDto5)

    game.run(msgDto1)
    game.run(msgDto2)
    game.run(msgDto3)
    game.run(msgDto4)
    game.run(msgDto5)
