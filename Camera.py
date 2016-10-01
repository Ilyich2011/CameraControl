from ctypes import *
from os.path import isfile
import numpy as np

#Error codes
DO_SNAP_ERROR = -503
CAMERA_IS_NOT_CONNECTED = -502
CAMERA_IS_ALREADY_CONNECTED = -501
NOT_IDLE_MODE = -504
NOT_LIVE_MODE = -505
NOT_CAPTURED_YET = -1

#States
CMODE_CLOSED = 0
CMODE_IDLE = 1
CMODE_LIVE = 2


class CCamera:
	def __init__(self,DllHandler):
		self.DllHandler=DllHandler
		self.Gain = 1
		self.Exp = 1
		self.X_dim = 1000
		self.Y_dim = 1000
		self.Bits = 1
		self.mode = 0 # 0 - closed, 1 - idle
		self.ErrorText = ""
	def GetGain(self):
		return self.Gain
	def GetExposition(self):
		return self.Exp
	def GetXdim(self):
		return self.X_dim
	def GetYdim(self):
		return self.Y_dim
	def GetBitsPerPixel(self):
		return self.Bits
	def GetMode(self):
		return self.mode
	def GetErrorDescription(self):
		return self.ErrorText
	def FormatFrameData(self): #It will write into ErrorText info about resolution and Bits per pixel
		self.ErrorText = "X: "+str(self.X_dim)+"\nY: "+str(self.Y_dim)+"\nBits: "+str(self.Bits)+"\nExposition: "+str(self.Exp)+" ms\nGain: "+str(self.Gain)

	def GetErrorDescriptionFromCode(self, ErrCode):
		self.DllHandler.GetLastErrorDescription.restype = c_char_p
		ed = self.DllHandler.GetLastErrorDescription(ErrCode)
		return ed.decode('ascii')
	
	def doSnap(self):
		if self.mode != CMODE_IDLE:
			self.ErrorText = "Not idle mode!"
			return DO_SNAP_ERROR		#Not idle mode
		frame = np.empty((self.X_dim, self.Y_dim), dtype = np.uint16)
		self.DllHandler.DoSnap.restype = c_int
		sr = self.DllHandler.DoSnap(np.ctypeslib.as_ctypes(frame))
		if (sr != self.X_dim*self.Y_dim):
			self.ErrorText = self.GetErrorDescriptionFromCode(sr)
			return DO_SNAP_ERROR
		return frame
	
	def Connect(self):
		if self.mode == CMODE_CLOSED:
			Xd = c_int()
			Yd = c_int()
			Bs = c_int()
			rn = self.DllHandler.CameraInit(byref(Xd),byref(Yd),byref(Bs))
			if rn != 0:
				self.ErrorText = self.GetErrorDescriptionFromCode(rn) #I should replace it with quering description of the error
				return rn
			else:
				self.X_dim = Xd.value
				self.Y_dim = Yd.value
				self.Bits = Bs.value
				self.mode = CMODE_IDLE
				self.FormatFrameData()
				return 0
		else:
			self.ErrorText = "Camera is already connected"
			return CAMERA_IS_ALREADY_CONNECTED
	
	def StartLiveAcquire(self):
		if (self.mode != CMODE_IDLE):
			self.ErrorText = "Not idle mode!"
			return NOT_IDLE_MODE
		rs = self.DllHandler.StartLiveAcquiring()
		if (rs!=0):
			self.ErrorText = self.GetErrorDescriptionFromCode(rs)
			return rs
		self.mode = CMODE_LIVE
		return 0
		
	def StopLiveAcquire(self):
		if (self.mode != CMODE_LIVE):
			self.ErrorText = "Not live mode!"
			return NOT_LIVE_MODE
		rs = self.DllHandler.StopAcquiring()
		if (rs!=0):
			self.ErrorText = self.GetErrorDescriptionFromCode(rs)
			return rs
		self.mode = CMODE_IDLE
		return 0
	
	def TryReadLiveFrame(self):
		if self.mode != CMODE_LIVE:
			self.ErrorText = "Not live mode!"
			return NOT_LIVE_MODE		#Not live mode
		frame = np.empty((self.X_dim, self.Y_dim), dtype = np.uint16)
		self.DllHandler.TryReadFrame.restype = c_int
		sr = self.DllHandler.TryReadFrame(np.ctypeslib.as_ctypes(frame))
		if (sr != self.X_dim*self.Y_dim):
			if sr != -1:
				self.ErrorText = self.GetErrorDescriptionFromCode(sr)
			else:
				self.ErrorText = "Frame is not captured yet"
			return sr
		return frame
	
	def Disconnect(self):
		if self.mode > 0:
			self.DllHandler.CameraClose()
			self.mode = CMODE_CLOSED
			self.ErrorText = "Connection is successfully closed"
			return 0
		else:
			self.ErrorText = "Camera is not connected"
			return CAMERA_IS_NOT_CONNECTED