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
    def __init__(self, mw, port):
        self.mw = mw
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
        print "received:", txt
        msg = json.loads(txt)
        cmd, data = msg["cmd"], msg["data"]

        # execute command
        getattr(AnkiServer, cmd)(self, data)

        # no error, so send ok back
        self.sock.write(QtCore.QByteArray("OK"))

    def addNote(self, data):
        "Takes model, deck, fields, tags. If deck is missing, use current deck."
        col = self.mw.col

        # get model and deck
        model = col.models.byName(data["model"])
        if not data["deck"]:
            deck_id = col.conf["curDeck"]
        else:
            deck_id = col.decks.id(data["deck"])

        # make note
        note = notes.Note(col, model=model)
        note.did = deck_id
        
        # you can specify fewer fields if you want, but not *more*
        if len(data["fields"]) > len(note.fields):
            raise Exception("received too many fields")
        for i, f in enumerate(data["fields"]):
            note.fields[i] = f
            
        if data["tags"]:
            for tag in data["tags"].split():
                note.addTag(tag)

        # add note
        col.addNote(note)    
        utils.tooltip("Note added.")

def startAnkiServer(mw, port):
    mw.ankiServer = AnkiServer(mw, port)

startAnkiServer(mw, PORT)
