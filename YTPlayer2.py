#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPalette, QKeySequence, QIcon
from PyQt5.QtCore import QDir, Qt, QUrl, QSize, QPoint, QTime, QMimeData, QProcess, QEvent
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaMetaData
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLineEdit,
                            QPushButton, QSizePolicy, QSlider, QMessageBox, QStyle, QVBoxLayout,  
                            QWidget, QShortcut, QMenu)
import sys
import os
import subprocess
#QT_DEBUG_PLUGINS

class VideoPlayer(QWidget):

    def __init__(self, aPath, parent=None):
        super(VideoPlayer, self).__init__(parent)

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.StreamPlayback)
        #self.mediaPlayer.mediaStatusChanged.connect(self.printMediaData)
        self.mediaPlayer.setVolume(100)
        self.videoWidget = QVideoWidget(self)
        
        self.lbl = QLineEdit('00:00:00')
        self.lbl.setReadOnly(True)
        self.lbl.setFixedWidth(70)
        self.lbl.setUpdatesEnabled(True)
        self.lbl.setStyleSheet(stylesheet(self))
        
        self.elbl = QLineEdit('00:00:00')
        self.elbl.setReadOnly(True)
        self.elbl.setFixedWidth(70)
        self.elbl.setUpdatesEnabled(True)
        self.elbl.setStyleSheet(stylesheet(self))

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setFixedWidth(32)
        #self.playButton.setStyleSheet("background: black")
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.positionSlider = QSlider(Qt.Horizontal, self)
        #self.positionSlider.setStyleSheet (stylesheet(self)) 
        self.positionSlider.setRange(0, 100)
        self.positionSlider.sliderMoved.connect(self.setPosition)
        self.positionSlider.sliderMoved.connect(self.handleLabel)
        self.positionSlider.setSingleStep(2)
        self.positionSlider.setPageStep(20)
        self.positionSlider.setAttribute(Qt.WA_TranslucentBackground, True)

        self.process = QProcess(self)
        self.process.readyRead.connect(self.dataReady)
        self.process.finished.connect(self.playFromURL)

        self.myurl = ""
        
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(5, 0, 5, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.lbl)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addWidget(self.elbl)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.videoWidget)
        layout.addLayout(controlLayout)

        self.setLayout(layout)
        #self.setFixedSize(480, 300)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        #self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.positionChanged.connect(self.handleLabel)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

        self.suspend_screensaver()

    def playFromURL(self):
        self.mediaPlayer.pause()
        self.mediaPlayer.setMedia(QMediaContent(QUrl(self.myurl)))
        self.playButton.setEnabled(True)
        self.positionSlider.setValue(0)
        self.mediaPlayer.play()
        print(self.myurl)

    def getYTUrl(self):
        cmd = "youtube-dl -g -f best " + self.myurl
        print("grabbing YouTube URL")
        self.process.start(cmd)

    def dataReady(self):
        self.myurl = str(self.process.readAll(), encoding = 'utf8').rstrip() ###
        self.myurl = self.myurl.partition("\n")[0]
        print(self.myurl)
        self.playFromURL()

    def suspend_screensaver(self):
        'suspend linux screensaver'
        proc = subprocess.Popen('gsettings set org.gnome.desktop.screensaver idle-activation-enabled false', shell=True)
        proc.wait()

    def resume_screensaver(self):
        'resume linux screensaver'
        proc = subprocess.Popen('gsettings set org.gnome.desktop.screensaver idle-activation-enabled true', shell=True)
        proc.wait()

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()
    
    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)
        
    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)
        mtime = QTime(0,0,0,0)
        mtime = mtime.addMSecs(self.mediaPlayer.duration())
        self.elbl.setText(mtime.toString())

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def handleError(self):
        self.playButton.setEnabled(False)
        print("Error: ", self.mediaPlayer.errorString())
    
    def forwardSlider(self):
        self.mediaPlayer.setPosition(self.mediaPlayer.position() + 1000*60)

    def forwardSlider10(self):
            self.mediaPlayer.setPosition(self.mediaPlayer.position() + 10000*60)

    def backSlider(self):
        self.mediaPlayer.setPosition(self.mediaPlayer.position() - 1000*60)

    def backSlider10(self):
        self.mediaPlayer.setPosition(self.mediaPlayer.position() - 10000*60)
        
    def volumeUp(self):
        self.mediaPlayer.setVolume(self.mediaPlayer.volume() + 10)
        print("Volume: " + str(self.mediaPlayer.volume()))
    
    def volumeDown(self):
        self.mediaPlayer.setVolume(self.mediaPlayer.volume() - 10)
        print("Volume: " + str(self.mediaPlayer.volume()))
        

    def printMediaData(self):
        if self.mediaPlayer.mediaStatus() == 6:
            if self.mediaPlayer.isMetaDataAvailable():
                res = str(self.mediaPlayer.metaData("Resolution")).partition("PyQt5.QtCore.QSize(")[2].replace(", ", "x").replace(")", "")
                print("%s%s" % ("Video Resolution = ",res))
            else:
                print("no metaData available")

##################### update Label ##################################
    def handleLabel(self):
            self.lbl.clear()
            mtime = QTime(0,0,0,0)
            self.time = mtime.addMSecs(self.mediaPlayer.position())
            self.lbl.setText(self.time.toString())
###################################################################

def stylesheet(self):
    return """
QLineEdit
{
background: transparent;
color: #888a85;
border: 0px;
font-size: 8pt;
font-weight: bold;
}
    """
