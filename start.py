import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QMessageBox
from PyQt5.QtCore import QCoreApplication, Qt, QTimer
from PyQt5.QtGui import QIntValidator
from mw import Ui_MaWi
from ctypes import *
from os.path import isfile
from Camera import *
import numpy as np
import pyqtgraph as pg
				
				
DELAY_TIMEOT = 20	#delay between reading frames in live mode in ms
		
		
class CLTimer(QTimer):
	def __init__(self,t_slot):
		super(CLTimer, self).__init__()
		self.timeout.connect(t_slot)
				
class CMainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.ui = Ui_MaWi()
		self.picture_window = 0
		self.ui.setupUi(self)
		self.ui.connect_button.clicked.connect(ConnectButtonHandler)
		self.ui.gain_input.setValidator(QIntValidator(1,3500))
		self.ui.gain_input.editingFinished.connect(self.GainChanged)
		self.ui.gain_slider.valueChanged.connect(self.GainChanged)
		self.ui.snap_button.clicked.connect(DoASnap)
		self.ui.live_button.clicked.connect(StartStopLive)

	def GainChanged(self):
		
		if self.sender().objectName() == "gain_input":
			self.ui.gain_slider.setValue(int(self.ui.gain_input.text()))
		else:
			self.ui.gain_input.setText(str(self.ui.gain_slider.value()))
	def forgetPicWind(self):
		self.picture_window = 0
def DisplayInfo(dtext):
	MMainWindow.ui.info_label.setText("Camera info:\n"+dtext)

def ConnectButtonHandler():
	if MCamera.GetMode() == CMODE_CLOSED:
		rn = MCamera.Connect()
		if rn != 0:
			QMessageBox.warning(MMainWindow, 'Error',MCamera.GetErrorDescription(), QMessageBox.Ok, QMessageBox.Ok)
		else:
			DisplayInfo(MCamera.GetErrorDescription())
			MMainWindow.ui.gain_input.setEnabled(True)
			MMainWindow.ui.gain_slider.setEnabled(True)
			MMainWindow.ui.connect_button.setText("Disconnect")
			MMainWindow.ui.snap_button.setEnabled(True)
			MMainWindow.ui.live_button.setEnabled(True)
	else:
		MCamera.Disconnect()
		DisplayInfo(MCamera.GetErrorDescription())
		MMainWindow.ui.gain_input.setEnabled(False)
		MMainWindow.ui.gain_slider.setEnabled(False)
		MMainWindow.ui.connect_button.setText("Connect")
		MMainWindow.ui.snap_button.setEnabled(False)
		MMainWindow.ui.live_button.setEnabled(False)

def TryFrame():
	sr = MCamera.TryReadLiveFrame()
	if (type(sr).__module__ != np.__name__):
		if (sr!=NOT_CAPTURED_YET):
			QMessageBox.warning(MMainWindow, 'Error',MCamera.GetErrorDescription(), QMessageBox.Ok, QMessageBox.Ok)
		return
	if (MMainWindow.picture_window == 0):
		MMainWindow.picture_window = pg.image(sr)
		MMainWindow.picture_window.setAttribute(Qt.WA_DeleteOnClose, True)
		MMainWindow.picture_window.destroyed.connect(MMainWindow.forgetPicWind)
	else:
		MMainWindow.picture_window.setImage(sr)

def StartStopLive():
	if MCamera.GetMode() == CMODE_IDLE:
		rn = MCamera.StartLiveAcquire()
		if rn != 0:
			QMessageBox.warning(MMainWindow, 'Error',MCamera.GetErrorDescription(), QMessageBox.Ok, QMessageBox.Ok)
		else:
			MMainWindow.ui.snap_button.setEnabled(False)
			MMainWindow.ui.live_button.setText("Unlive")
			MTimer.start(DELAY_TIMEOT)
	else:
		rn = MCamera.StopLiveAcquire()
		if rn != 0:
			QMessageBox.warning(MMainWindow, 'Error',MCamera.GetErrorDescription(), QMessageBox.Ok, QMessageBox.Ok)
		else:
			MMainWindow.ui.snap_button.setEnabled(True)
			MMainWindow.ui.live_button.setText("Live")
			MTimer.stop()
		
		
def DoASnap():
	sr = MCamera.doSnap()
	if (type(sr).__module__ != np.__name__):
		QMessageBox.warning(MMainWindow, 'Error',MCamera.GetErrorDescription(), QMessageBox.Ok, QMessageBox.Ok)
		return
	if (MMainWindow.picture_window == 0):
		MMainWindow.picture_window = pg.image(sr)
		MMainWindow.picture_window.setAttribute(Qt.WA_DeleteOnClose, True)
		MMainWindow.picture_window.destroyed.connect(MMainWindow.forgetPicWind)
	else:
		MMainWindow.picture_window.setImage(sr)
		
if __name__ == '__main__':
	FalconDll=windll.LoadLibrary("FalconBlue.dll")
	MCamera = CCamera(FalconDll)
	app = QApplication(sys.argv)
	MMainWindow = CMainWindow()
	MTimer = CLTimer(TryFrame)
	MMainWindow.show()
	sys.exit(app.exec_())
