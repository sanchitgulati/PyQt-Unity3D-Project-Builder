from PyQt5.QtWidgets import QSpacerItem, QApplication, QWidget, QPushButton, QGroupBox , QVBoxLayout, QLabel, QTextEdit, QMessageBox, QFileDialog
from PyQt5 import QtCore,QtWidgets,QtGui
import sys,os
import subprocess
import threading
from os import path



class GitUpdate(QtCore.QThread):

    output = QtCore.pyqtSignal(object)
    finished = QtCore.pyqtSignal()

    def __init__(self, gitPath):
        QtCore.QThread.__init__(self)
        self.gitPath = gitPath

    def run(self):
        process = subprocess.Popen(['git','-C',self.gitPath, 'pull'], stdout=subprocess.PIPE,universal_newlines=True)
        while True:
            line = process.stdout.readline().strip()
            print(line)
            self.output.emit(line)
            return_code = process.poll()
            if return_code is not None:
                self.finished.emit()
                break

class UnityBuildUpdate(QtCore.QThread):

    output = QtCore.pyqtSignal(object)
    finished = QtCore.pyqtSignal()

    def __init__(self, unityPath, unitySource,buildDirectory):
        QtCore.QThread.__init__(self)
        self.unityPath = unityPath
        self.unitySource = unitySource
        self.buildDirectory = buildDirectory

    def run(self):
        process = subprocess.Popen([self.unityPath,'-quit','-batchmode','-nographics', '-projectPath',self.unitySource,'-executeMethod','BuildAutomation.BuildApplication','-buildPath',self.buildDirectory], stdout=subprocess.PIPE,universal_newlines=True)
        while True:
            line = process.stdout.readline().strip()
            print(line)
            self.output.emit(line)
            return_code = process.poll()
            if return_code is not None:
                self.finished.emit()
                break

class UnityBuildTool(QWidget):


    def SetupErrorGroup(self):
        box = QGroupBox("Error:")
        vbox = QVBoxLayout()
        box.setLayout(vbox)
        
        self.errorLabel = QLabel()
        self.errorLabel.setText("")
        vbox.addWidget(self.errorLabel)


        self.layout.addWidget(box)

    def SetupUnityInstallFolder(self,callback):
        box = QGroupBox("Unity:")
        vbox = QVBoxLayout()
        box.setLayout(vbox)

        button = QPushButton("Change Unity Install Directory")
        button.clicked.connect(callback)
        vbox.addWidget(button)

        self.installLabel = QLabel()
        self.installLabel.setText(self.settings.value('fUnityDir',"Not Set", str))
        vbox.addWidget(self.installLabel)

        self.layout.addWidget(box)

    def SetupGameSourceFolder(self,callback):
        box = QGroupBox("Git Directory (Seperate copy from working Directory):")
        vbox = QVBoxLayout()
        box.setLayout(vbox)
        
        button = QPushButton("Change Git Directory")
        button.clicked.connect(callback)
        vbox.addWidget(button)
        note = QLabel()
        note.setText("*Will call static function at BuildAutomation.BuildApplication in your project")
        vbox.addWidget(note)


        self.gameSourceLabel = QLabel()
        self.gameSourceLabel.setText(self.settings.value('fGameSource',"Not Set", str))
        vbox.addWidget(self.gameSourceLabel)
        self.layout.addWidget(box)

    def SetupBuildFolder(self,callback):
        
        box = QGroupBox("Build folder:")
        vbox = QVBoxLayout()
        box.setLayout(vbox)


        button = QPushButton("Change Build Folder")
        button.clicked.connect(callback)
        vbox.addWidget(button)


        self.buildLabel = QLabel()
        self.buildLabel.setText(self.settings.value('fBuildFolder',"Not Set", str))
        vbox.addWidget(self.buildLabel)
        self.layout.addWidget(box)


    def SetupBuildButton(self,callback):

        box = QGroupBox("Build folder:")
        vbox = QVBoxLayout()
        box.setLayout(vbox)


        button = QPushButton("Build Game")
        button.clicked.connect(callback)
        vbox.addWidget(button)


        self.buildStatusLabel = QLabel()
        self.buildStatusLabel.setText("Status : Idle")
        vbox.addWidget(self.buildStatusLabel)
        self.layout.addWidget(box)


    def SetupLogWindow(self):

        box = QGroupBox("Logs:")
        vbox = QVBoxLayout()
        box.setLayout(vbox)


        self.textEdit = QTextEdit()
        vbox.addWidget(self.textEdit)
        self.layout.addWidget(box)


    def __init__(self, parent = None):
        super(UnityBuildTool, self).__init__(parent)
        self.errorList = {}
        self.settings = QtCore.QSettings('sanchitgulati', 'unity_builder')
        self.setGeometry(300, 500, 300, 150)
        self.layout = QVBoxLayout()

        self.SetupErrorGroup()
        self.SetupUnityInstallFolder(self.getUnityInstallFolder)
        self.SetupGameSourceFolder(self.getGameSourceFolder)
        self.SetupBuildFolder(self.setBuildFolder)
        self.SetupLogWindow()
        

        verticalSpacer = QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.layout.addSpacerItem(verticalSpacer)


        self.SetupBuildButton(self.BuildGame)

        self.setLayout(self.layout)
        self.setWindowTitle("Unity Build Tool")

    def getUnityInstallFolder(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.settings.setValue('fUnityDir',folder)
        self.installLabel.setText(folder)
        dirUnity = os.path.join(folder,'Unity.exe')
        if(path.exists(dirUnity)):
            if self.errorList.get('Unity'): self.errorList.pop('Unity')
        else:
            self.errorList['Unity'] = "Not a Unity Install Directory"
        self.parseErrorList()

    def parseErrorList(self):
        self.errorLabel.setText("")
        for x, y in self.errorList.items():
            self.errorLabel.setText(self.errorLabel.text() + '\n' + y)

    def getGameSourceFolder(self, *args):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.settings.setValue('fGameSource', folder)
        self.gameSourceLabel.setText(folder)

        dirAssets = os.path.join(folder,'Assets')
        dirProjectSettings = os.path.join(folder,'ProjectSettings')
        dirGit = os.path.join(folder,'.git')
        if(path.exists(dirAssets)):
            if self.errorList.get('Assets'): self.errorList.pop('Assets')
        else:
            self.errorList['Assets'] = "Not a Unity Project - Missing Assets Folder"

        if(path.exists(dirProjectSettings)):
            if self.errorList.get('ProjectSettings'): self.errorList.pop('ProjectSettings')
        else:
            self.errorList['ProjectSettings'] = "Not a Unity Project - Missing ProjectSettings Folder"
        if(path.exists(dirGit)):
            if self.errorList.get('Git'): self.errorList.pop('Git')
        else:
            self.errorList['Git'] = "Not a Git Repo, Won't be able to git pull"

        self.parseErrorList()

    def setBuildFolder(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.settings.setValue('fBuildFolder',folder)
        self.buildLabel.setText(folder)


    def BuildGame(self):
        self.buildStatusLabel.setText("Status : Updating GIT")
        self.QThreadGitUpdate = GitUpdate(self.settings.value('fGameSource',"", str))
        self.QThreadGitUpdate.output.connect(self.onDataEmitted)
        self.QThreadGitUpdate.finished.connect(self.onGitUpdated)
        self.QThreadGitUpdate.start()

    def onDataEmitted(self, data):
        self.textEdit.insertPlainText(data)
        self.textEdit.insertPlainText('\n')
        self.textEdit.moveCursor(QtGui.QTextCursor.End)

    def onBuildFinish(self):
        self.buildStatusLabel.setText("Status : Build Done")

    def onGitUpdated(self):
        self.buildStatusLabel.setText("Status : Building with Unity")
        unityDir = self.settings.value('fUnityDir',"", str)
        unityExe = os.path.join(unityDir,'Unity.exe')
        unitySource = self.settings.value('fGameSource',"", str)
        buildDir = self.settings.value('fBuildFolder',"Not Set", str)
        
        self.QThreadUnityBuild = UnityBuildUpdate(unityExe,unitySource,buildDir)
        self.QThreadUnityBuild.output.connect(self.onDataEmitted)
        self.QThreadUnityBuild.finished.connect(self.onBuildFinish)
        self.QThreadUnityBuild.start()
    
def main():
   app = QApplication(sys.argv)
   app.setWindowIcon(QtGui.QIcon('icon.jpg'))
   ex = UnityBuildTool()
   ex.show()
   sys.exit(app.exec_())
	
if __name__ == '__main__':
   main()