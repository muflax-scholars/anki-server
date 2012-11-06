# -*- coding: utf-8 -*-
# Copyright muflax <mail@muflax.com>, 2012
# License: GNU GPL 3 <http://www.gnu.org/copyleft/gpl.html>

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui
import PyQt4.QtNetwork as QtNetwork

import os, copy, shutil, tempfile, time
import json

from aqt import mw, utils
from anki import notes, consts

PORT = 49666

class AnkiServer(object):
    def __init__(self, port):
        self.tcpServer = QtNetwork.QTcpServer()
        self.tcpServer.listen(address=QtNetwork.QHostAddress.LocalHost, port=port)
        QtCore.QObject.connect(self.tcpServer, QtCore.SIGNAL("newConnection()"),
                               self.newConnectionArrives)

    
    def newConnectionArrives(self):
        self.sock = self.tcpServer.nextPendingConnection()
        QtCore.QObject.connect(self.sock, QtCore.SIGNAL("readyRead()"),
                               self.tcpSocketReadyReadEmitted)
        
    def tcpSocketReadyReadEmitted(self):
        txt = str(self.sock.readAll())
        self.parseCommand(txt)

    def parseCommand(self, txt):
        # parse cmd
        msg = json.loads(txt)
        cmd, data = msg["cmd"], msg["data"]

        # execute command
        getattr(AnkiServer, cmd)(self, data)

    def addNotes(self, data):
        print data
        

def startAnkiServer(self, port):
    self.ankiServer = AnkiServer(port)

startAnkiServer(mw, PORT)
