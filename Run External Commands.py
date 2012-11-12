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
from anki.utils import fieldChecksum, splitFields
from anki.hooks import addHook

# TODO split in multiple files

PORT = 49666

class AnkiServer(object):
    def __init__(self, col):
        self.col = col
        self.tcpServer = QtNetwork.QTcpServer()
        self.tcpServer.listen(address=QtNetwork.QHostAddress.LocalHost, port=PORT)
        QtCore.QObject.connect(self.tcpServer, QtCore.SIGNAL("newConnection()"), self.newConnectionArrives)

    
    def newConnectionArrives(self):
        self.sock = self.tcpServer.nextPendingConnection()
        QtCore.QObject.connect(self.sock, QtCore.SIGNAL("readyRead()"),
                               self.tcpSocketReadyReadEmitted)
        
    def tcpSocketReadyReadEmitted(self):
        txt = str(self.sock.readAll())
        self.parseCommand(txt)

    def parseCommand(self, txt):
        # parse cmd
        # print "received:", txt
        msg = json.loads(txt)
        cmd = msg["cmd"]
        data = msg.get("data", None)

        # execute command
        ret = getattr(AnkiServer, cmd)(self, data)
        
        # send back return code
        self.sock.write(QtCore.QByteArray(json.dumps(ret)))

    def addNote(self, data):
        "Takes model, deck, fields, tags. If deck is missing, use current deck."
        col = self.col

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
        col.save()
        utils.tooltip("Note added.")
        return True

    def addFile(self, data):
        "Takes path, adds file to media dir."
        # TODO assumes file is local, should allow alternatives
        return self.col.media.addFile(data["path"])

    def mediaDir(self, data):
        "Takes no info, returns path to media dir."
        return self.col.media.dir()
        
    def isDupe(self, data):
        "Takes field, model and returns True if the field is a dupe and False otherwise."
        # find any matching csums and compare
        csum = fieldChecksum(data["field"])
        mid = self.col.models.byName(data["model"])["id"]
        for flds in self.col.db.list(
                "select flds from notes where csum = ? and id != ? and mid = ?",
                csum, 0, mid):
            if splitFields(flds)[0] == data["field"]:
                return True
        return False

    def models(self, data):
        "Takes no info, returns list of all models as individual dicts."
        return self.col.models.all()

    def modelByName(self, data):
        "Takes name, returns model dict."
        return self.col.models.byName(data["name"])

    def decks(self, data):
        "Takes no info, returns list of all decks as individual dicts"
        return self.col.decks.all()

    def deckByName(self, data):
        "Takes name, returns deck dict."
        return self.col.decks.byName(data["name"])

    def tags(self, data):
        "Takes no info, returns list of tags."
        return self.col.tags.all()
        
        
def startAnkiServer():
    print "starting API server..."
    mw.ankiServer = AnkiServer(mw.col)

# wait until col is ready
addHook("profileLoaded",  startAnkiServer)
