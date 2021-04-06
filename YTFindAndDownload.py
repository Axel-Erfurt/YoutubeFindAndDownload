#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Credits: youtube-search-python made by Hitesh Kumar Saini https://github.com/alexmercerind/youtube-search-python
# MIT License
#############################################################################
from PyQt5.QtCore import (QFile, QStandardPaths, Qt, QProcess, QSettings)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (QApplication, QFileDialog, QMainWindow, QLineEdit, QAction, 
                             QProgressBar, QTableWidget, QAbstractItemView, QDockWidget, 
                             QMessageBox, QHBoxLayout, QVBoxLayout, QWidget, QLabel, 
                             QPushButton, QComboBox, QTableWidgetItem)
            
from youtubesearchpython import VideosSearch
import YTPlayer2 as YTPlayer


findList = []

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        btnwidth = 160
        self.ytdlExec = ""
        self.ytUrl = ''
        self.OutFolder = '/tmp'
        self.settings = QSettings('YouTubeDLS', 'YTDL')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.createStatusBar()
        pyfile = QStandardPaths.findExecutable("youtube-dl")
        if not pyfile == "":
            print("found " + pyfile)
            self.ytdlExec = pyfile
        else:
            self.msgbox("youtube-dl not found\nPlease install youtube-dl")

        self.cmd = ''
        self.process = QProcess(self)
        self.process.started.connect(lambda: self.showMessage("creating List"))
        self.process.finished.connect(lambda: self.showMessage("finished creating List"))
        self.process.finished.connect(self.processFinished)
        self.process.readyRead.connect(self.processOut)

        self.dlProcess = QProcess(self)
        self.dlProcess.setProcessChannelMode(QProcess.MergedChannels)
        self.dlProcess.started.connect(lambda: self.showMessage("download started"))
        self.dlProcess.finished.connect(lambda: self.showMessage("download finished"))
        self.dlProcess.finished.connect(lambda: self.setWindowTitle("YouTube Find & Download"))
        self.dlProcess.readyRead.connect(self.dlProcessOut)

        self.list = []
        
        self.setContentsMargins(0,0,15,5)

        self.move(0, 0)
        self.setFixedSize(1080, 660)
        self.setStyleSheet(myStyleSheet(self))
        self.setWindowIcon(QIcon.fromTheme("youtube"))
        #### path
        lblFind = QLabel()
        lblFind.setText("find:")
        lblFind.setAlignment(Qt.AlignRight)
        lblFind.setFixedWidth(btnwidth)
        lblFind.setFont(QFont("Noto Sans", 9))
        lblFind.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        
        ### search entry
        self.findField = QLineEdit("")
        self.findField.addAction(QIcon.fromTheme("edit-find"), 0)
        self.nextAction = QAction(QIcon.fromTheme("go-next"), None, None)
        self.nextAction.setToolTip("next page")
        self.nextAction.triggered.connect(self.searchNextPage)
        self.findField.addAction(self.nextAction, 1)
        self.findField.setPlaceholderText("insert search term and press ENTER \
                                           to get list of available movies")
        self.findField.setToolTip("insert search term and press ENTER \
                                    to get list of available movies")
        self.findField.returnPressed.connect(self.findItems)

        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()
        vlayout.addWidget(self.findField)
        
        self.lb = QTableWidget()
        self.lb.setGridStyle(1)
        self.lb.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lb.setDragDropMode(QAbstractItemView.DragOnly)
        self.lb.setToolTip("on selection change the Youtube ID is in clipboard\n\
                            double click to create list of available resolutions for  download")
        self.lb.setColumnCount(3)
        self.lb.setColumnWidth(0, 420)
        self.lb.setColumnWidth(2, 88)
        self.lb.hideColumn(1)
        self.lb.horizontalHeader().stretchLastSection()
        self.lb.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lb.doubleClicked.connect(self.getItem)
        self.lb.itemSelectionChanged.connect(self.copyURL)
        self.lb.setHorizontalHeaderLabels(["Title", "ID", "Duration"])
        self.lb.setFixedHeight(380)
        #self.lb.setFixedWidth(544)
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.lb)

        #### output path
        btnOutPath = QPushButton()
        btnOutPath.setFont(QFont("Noto Sans", 9))
        btnOutPath.setIcon(QIcon.fromTheme("gtk-open"))
        btnOutPath.setText("select Output Folder")
        btnOutPath.setFixedWidth(btnwidth)
        btnOutPath.clicked.connect(self.openOutFolder)
        self.lblOutPath = QLineEdit()
        self.lblOutPath.setPlaceholderText("insert output folder path")
        self.lblOutPath.textChanged.connect(self.updateOutputPath)

        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(btnOutPath)
        hlayout2.addWidget(self.lblOutPath)

        #### ytdlExec path
        btnYTDLpath = QPushButton()
        btnYTDLpath.setFont(QFont("Noto Sans", 9))
        btnYTDLpath.setIcon(QIcon.fromTheme("document-open"))
        btnYTDLpath.setText("select youtube-dl")
        btnYTDLpath.setFixedWidth(btnwidth)
        btnYTDLpath.clicked.connect(self.selectYTDL)
        self.lblYTDLpath = QLineEdit(str(self.ytdlExec))
        self.lblYTDLpath.textChanged.connect(self.updatelblYTDLpath)
        self.lblYTDLpath.setPlaceholderText("insert path to youtube-dl")


        hlayout3 = QHBoxLayout()
        hlayout3.addWidget(btnYTDLpath)
        hlayout3.addWidget(self.lblYTDLpath)

        dlBtn = QPushButton()
        dlBtn.setIcon(QIcon.fromTheme("download"))
        dlBtn.setText("Download")
        dlBtn.clicked.connect(self.downloadSelected)
        dlBtn.setFixedWidth(100)

        dlCancelBtn = QPushButton()
        dlCancelBtn.setIcon(QIcon.fromTheme("cancel"))
        dlCancelBtn.setText("Cancel")
        dlCancelBtn.clicked.connect(self.cancelDownload)
        dlCancelBtn.setFixedWidth(100)
        
        empty = QWidget()
        
        playBtn = QPushButton()
        playBtn.setIcon(QIcon.fromTheme("media-playback-start"))
        playBtn.setText("Play")
        playBtn.clicked.connect(self.playMovie)
        playBtn.setFixedWidth(100)

        self.dlCombo = QComboBox()
        self.dlCombo.setFixedHeight(26)

        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(12)
        self.pbar.setFont(QFont("Helvetica", 7))
        self.pbar.setMaximum(100)
        self.pbar.setMinimum(0)
        self.pbar.setValue(0)

        btnLayout = QHBoxLayout()
        btnLayout.addWidget(dlBtn)
        btnLayout.addWidget(dlCancelBtn)
        btnLayout.addWidget(empty)
        btnLayout.addWidget(playBtn)

        vlayout.addLayout(hlayout2)
        vlayout.addLayout(hlayout3)
        vlayout.addWidget(self.dlCombo)
        vlayout.addWidget(self.pbar)
        vlayout.addLayout(btnLayout)

        mywidget = QWidget()
        mywidget.setLayout(vlayout)
        
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(mywidget)
        
        self.player = YTPlayer.VideoPlayer('')
        self.playerbox = QVBoxLayout()
        self.playerbox.addWidget(self.player)
        
        self.dwid = QDockWidget("  Player")
        self.dwid.setStyleSheet("background: black")
        self.dwid.topLevelChanged.connect(self.makeFloating)
        self.dwid.setFeatures(QDockWidget.DockWidgetFloatable)
        self.dwid.setFixedSize(480, 320)
        self.pwid = QWidget()
        self.pwid.setStyleSheet("background: black")
        self.pwid.setLayout(self.playerbox)
        self.dwid.setWidget(self.pwid)
        
        self.cwid = QWidget()
        self.cwid.setLayout(self.hbox)

        self.setCentralWidget(self.cwid)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dwid)

        self.clip = QApplication.clipboard()

        self.readSettings()
        self.setWindowTitle("YouTube Find & Download")
        
    def makeFloating(self):
        #return
        if self.dwid.isFloating() == False:
            self.dwid.setFixedSize(480, 320)
        else:
            g = QApplication.desktop().screenGeometry()
            self.dwid.setFixedSize(g.width(), g.height() - 30)
            self.dwid.move(0, 0)
        
    def mouseDoubleClickEvent(self, event):
        if self.player.underMouse():
            if event.button() == Qt.LeftButton:
                if self.dwid.isFloating() == False:
                    self.dwid.setFloating(True)
                    g = QApplication.desktop().screenGeometry()
                    self.dwid.setFixedSize(g.width(), g.height() - 30)
                    self.dwid.move(0, 0)

        
    def playMovie(self):
        row = self.selectedRow()
        item = self.lb.item(row, 1 ).text()
        if not item == None:
            if self.player:
                self.player.myurl = item
                self.player.getYTUrl()
                #self.fillCombo(item)
            else:
                print("player already visible")
            
        
    def dragMoveEvent(self, event):
        if event.source() == self.lb:
            if event.buttons() & Qt.LeftButton:
                row = self.selectedRow()
                item = self.lb.item(row, 1 ).text()
                if not item == None:
                    name = item
                    print(name)
                    print(event.mimeData().text())
                event.accept()
        else:
            print("not lb")
        
    def findItems(self):
        self.lb.clearContents()
        self.lb.setRowCount(0)
        searchText = self.findField.text().replace(" ", "+")
        self.videosSearch = VideosSearch(searchText)
        res = self.videosSearch.result()
        a = 0
        if res:
            for x in res['result']:
                title = x["title"]
                url = x["id"]
                duration = x["duration"]
                #print(title, url)
                findList.append(url)
                self.lb.insertRow(a)
                t = QTableWidgetItem(title)
                u = QTableWidgetItem(url)
                d = QTableWidgetItem(duration)
                d.setTextAlignment(Qt.AlignRight)
                self.lb.setItem(a, 0, t)
                self.lb.setItem(a, 1, u)
                self.lb.setItem(a, 2, d)
                a += 1
            for x in range(self.lb.rowCount()):
                self.lb.resizeRowToContents(x)
            self.lb.selectRow(0)
                
    def searchNextPage(self):
        if self.lb.rowCount() > 0:
            self.lb.clearContents()
            self.lb.setRowCount(0)
            self.videosSearch.next()
            res = self.videosSearch.result()
            a = 0
            if res:
                for x in res['result']:
                    title = x["title"]
                    url = x["id"]
                    duration = x["duration"]
                    findList.append(url)
                    self.lb.insertRow(a)
                    t = QTableWidgetItem(title)
                    u = QTableWidgetItem(url)
                    d = QTableWidgetItem(duration)
                    d.setTextAlignment(Qt.AlignRight)
                    self.lb.setItem(a, 0, t)
                    self.lb.setItem(a, 1, u)
                    self.lb.setItem(a, 2, d)
                    a += 1
                for x in range(self.lb.rowCount()):
                    self.lb.resizeRowToContents(x)  
                self.lb.selectRow(0)
                
    def closeEvent(self, e):
        self.writeSettings()
        e.accept()

    def readSettings(self):
        print("reading settings")
        if self.settings.contains('geometry'):
            self.setGeometry(self.settings.value('geometry'))
        if self.settings.contains('outFolder'):
            self.lblOutPath.setText(self.settings.value('outFolder'))

    def writeSettings(self):
        print("writing settings")
        self.settings.setValue('outFolder', self.OutFolder)
        self.settings.setValue('geometry', self.geometry())

    def updateOutputPath(self):
        self.OutFolder = self.lblOutPath.text()
        self.showMessage("output path changed to: " + self.lblOutPath.text())

    def updatelblYTDLpath(self):
        self.ytdlExec = self.lblYTDLpath.text()
        self.showMessage("youtube-dl path changed to: " +self.lblYTDLpath.text())

    def showMessage(self, message):
        self.statusBar().showMessage(message, 0)

    def selectYTDL(self):
         fileName,_ = QFileDialog.getOpenFileName(self, "locate ytdlExec", "/usr/local/bin/ytdlExec",  "exec Files (*)")
         if fileName:
            self.lblYTDLpath.setText(fileName)
            self.ytdlExec = fileName

    def openOutFolder(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        fileName = dlg.getExistingDirectory()
        if fileName:
            self.lblOutPath.setText(fileName)
            
    def getItem(self):
        row = self.selectedRow()
        item = self.lb.item(row, 1 ).text()
        #column = 1
        if not item == None:
            name = item
            self.fillCombo(name)
        else:
            name = ""

    def copyURL(self):
        row = self.selectedRow()
        if row:
            item = self.lb.item(row, 1 ).text()
            self.clip.setText(item)

    def selectedRow(self):
        if self.lb.selectionModel().hasSelection():
            row =  self.lb.selectionModel().selectedIndexes()[0].row()
            return int(row)

    def selectedColumn(self):
        column =  self.lb.selectionModel().selectedIndexes()[0].column()
        return int(column)


    def fillCombo(self, name):
        self.dlCombo.clear()
        if QFile.exists(self.ytdlExec):
            self.list = []
            self.ytUrl = name
            if not name == "":
                print("fill Combo")
                self.process.start(self.ytdlExec,['-F', self.ytUrl])
        else:
            self.showMessage("youtube-dl missing")
        
    def processOut(self):
            try:
                output = str(self.process.readAll(), encoding = 'utf8').rstrip()
            except Error:
                output = str(self.process.readAll()).rstrip()          
            self.list.append(output)

    def processFinished(self):
            out = ','.join(self.list)
            out = out.partition("resolution note")[2]
            out = out.partition('\n')[2]
            mylist = out.rsplit('\n')
            self.dlCombo.addItems(mylist)
            count = self.dlCombo.count()
            self.dlCombo.setCurrentIndex(count-1)

    def downloadSelected(self):
        if QFile.exists(self.ytdlExec):
            self.pbar.setValue(0)
            quality = self.dlCombo.currentText().partition(" ")[0]
            options = []
            options.append('-f')
            options.append(quality)
            options.append('--add-metadata')
            options.append("-o")
            options.append("%(title)s.%(ext)s")
            options.append(self.ytUrl)
            if not quality == "":
                self.showMessage("download started")
                print("download selected quality:", quality)
                self.dlProcess.setWorkingDirectory(self.OutFolder)
                self.dlProcess.start(self.ytdlExec, options)
            else:
                self.showMessage("list of available files is empty")
        else:
           self.showMessage("youtube-dl missing")

    def dlProcessOut(self):
        try:
            out = str(self.dlProcess.readAll(), encoding = 'utf8').rstrip()
        except Error:
            out = str(self.dlProcess.readAll()).rstrip()
        out = out.rpartition("[download] ")[2]
        self.showMessage("Progress: " + out)
        self.setWindowTitle(out)
        out = out.rpartition("%")[0].rpartition(".")[0]
        if not out == "":
            try:
               pout = int(out)
               self.pbar.setValue(pout)
            except ValueError:
                pass

    def cancelDownload(self):
        if self.dlProcess.state() == QProcess.Running:
            print("process is running, will be cancelled")
            self.dlProcess.close()
            self.showMessage("Download cancelled")
            self.pbar.setValue(0)
        else:
            self.showMessage("process is not running")

    def createStatusBar(self):
        self.statusBar().showMessage("Ready")

    def msgbox(self, message):
        QMessageBox.warning(self, "Message", message)

def myStyleSheet(self):
    return """

QStatusBar
{
    font-family: Helvetica;
    font-size: 8pt;
    color: #666666;
}
QMenuBar
{
    background: transparent;
    border: 0px;
}
QToolBar
{
    background: transparent;
    border: 0px;
}
QMainWindow
{
     background: qlineargradient(y1: 0, y2: 1,
                                 stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                 stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
}
QTableWidget
{
    background: qlineargradient(y1: 0, y2: 1,
                                 stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                 stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
    color: #222222;
    font-size: 9pt;
    gridline-color: gray;
}


QHeaderView::section
{
    background-color:#d3d7cf;
    color: #204a87; 
    font: bold
}
QHeaderView
{
     background: qlineargradient(y1: 0, y2: 1,
                                 stop: 0 #E1E1E1, stop: 1.0 #D3D3D3);
}
QTableCornerButton::section 
{
    background-color:#d3d7cf; 
}
QLineEdit
{
     background: qlineargradient(y1: 0, y2: 1,
                                 stop: 0 #E1E1E1, stop: 0.4 #e5e5e5,
                                 stop: 0.5 #e9e9e9, stop: 1.0 #d2d2d2);
}
QPushButton
{
    background: #babdb6;
}
QComboBox
{
    background: #babdb6;
}
QSlider::handle:horizontal 
{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #333, stop:1 #555555);
    width: 14px;
    border-radius: 0px;
}
    QSlider::groove:horizontal {
    border: 1px solid #444;
    height: 10px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #000, stop:1 #222222);
}

    """    


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
