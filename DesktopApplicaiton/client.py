#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 11:42:35 2020

@author: Harry
"""

import sys
if sys.version_info.major < 3 or sys.version_info.minor < 4:
    raise RuntimeError('At least Python 3.4 is required')
    
import time, http.client
from PyQt5 import QtCore, uic, QtWidgets
import icons_rc
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap
from urllib.request import urlopen
import requests
import dubins_path_planning as dubins
import math
import numpy as np


login_screen = "login_screen.ui"
running_screen = "running_screen.ui"
setting_screen = "setting_screen.ui"
calibrate_screen = "calibrate_screen.ui"

#Ui files
Ui_Login_screen, QtBaseClass = uic.loadUiType(login_screen)
Ui_Running_screen, QtBaseClass = uic.loadUiType(running_screen)
Ui_Setting_screen, QtBaseClass = uic.loadUiType(setting_screen)
Ui_Calibrate_screen, QtBaseClass = uic.loadUiType(calibrate_screen)

#Speed levels
MAX_SPEED = 100
MIN_SPEED = 50
SPEED_LEVEL_1 = MIN_SPEED
SPEED_LEVEL_2 = (MAX_SPEED - MIN_SPEED) /4 * 1 + MIN_SPEED
SPEED_LEVEL_3 = (MAX_SPEED - MIN_SPEED) /4 * 2 + MIN_SPEED
SPEED_LEVEL_4 = (MAX_SPEED - MIN_SPEED) /4 * 3 + MIN_SPEED
SPEED_LEVEL_5 = MAX_SPEED
SPEED = [0, SPEED_LEVEL_1, SPEED_LEVEL_2, SPEED_LEVEL_3, SPEED_LEVEL_4, SPEED_LEVEL_5]

HOST = '192.168.0.133'
PORT = '8000'
autologin = 1

BASE_URL = 'http://' + HOST + ':' + PORT + '/'

def refresh_url():
    global BASE_URL
    BASE_URL = 'http://' + HOST + ':' + PORT + '/'

def __read_auto_inf__():
    try:
        fp = open("auto_ip.inf", 'r')
        lines = fp.readlines()
        for line in lines:
            if "ip" in line:
                ip = line.replace(' ', '').replace('\n','').split(':')[1]
                
            elif "port" in line:
                port = line.replace(' ', '').replace('\n','').split(':')[1]
            
            elif "remember_status" in line:
                remember_status = line.replace(' ', '').replace('\n', '').split(':')[1]
        fp.close
        return ip,port, int(remember_status)
    except IOError:
        return -1
    
def __write_auto_inf__ (ip = None, port = None, rem_status = None):
    fp = open("auto_ip.inf", 'w')
    string = "ip: %s \nport: %s\nremember_status: %s\n" %(ip, port, rem_status)
    fp.write(string)
    fp.close()
    
class LoginScreen(QtWidgets.QDialog, Ui_Login_screen):
    #Login Screen GUI, inherit from Ui_Login_screen define control functions.
    
    def __init__(self):
        global autologin
        global HOST, PORT
        
        info = __read_auto_inf__()
        if info == -1:
            HOST = ''
            PORT = ''
            autologin = -1
        else:
            HOST = info[0]
            PORT = info[1]
            autologin = info[2]
        QtWidgets.QDialog.__init__(self)
        Ui_Login_screen.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("Log In - SunFounder PiCar-V Client")
        
        if autologin == 1:
            self.lEd_host.setText(HOST)
            self.label_Error.setText("")
            self.pBtn_checkbox.setStyleSheet("border-image: url(./images/check2.png);")
        else:
            self.lEd_host.setText("")
            self.label_Error.setText("")
            self.pBtn_checkbox.setStyleSheet("border-image: url(./images/uncheck1.png);")
        
        self.pBtn_checkbox.clicked.connect(self.on_pBtn_checkbox_clicked)
        
    def on_pBtn_login_clicked(self):
        #The login button clicked, this function will run. This function use for logining,
		#first, check the length of text in line edit, if ok, saved them to variable HOST 
		#and PORT, after that, call function connection_ok(), if get 'OK' return, login 
		#succeed, close this screen, show running screen
        
        global HOST, PORT
        
        if 7 < len(self.lEd_host.text()) < 16:
            HOST = self.lEd_host.text()
            PORT = self.lEd_port.text()
            refresh_url()
            self.label_Error.setText("Connecting to Robot")
            
            if connection_ok() == True:
                if autologin == 1:
                    HOST = self.lEd_host.text()
                    PORT = self.lEd_port.text()
                else:
                    self.lEd_host.setText("")
                    self.label_Error.setText("")
                
                __write_auto_inf__(HOST, PORT, autologin)
                self.label_Error.setText("")
                
                login1.close()
                running1.start_stream()
                running1.show()
                return True
            else:
                self.label_Error.setText("Failed to connect")
                return False
        else:
            self.label_Error.setText("Host or port incorrect")
            return False
        print ("on_pBtn_login_clicked", HOST, PORT, autologin, "\n")
        
    def on_pBtn_login_pressed(self):
        self.pBtn_login.setStyleSheet("border-image: url(./images/login_button_pressed.png; color: rgb(54, 69, 79);")
    
    def on_pBtn_login_released(self):
        self.pBtn_login.setStyleSheet("border-image: url(./images/login_button_unpressed.png; color: rgb(54, 69, 79);")
    
    def on_pBtn_checkbox_clicked(self):
        #The checkbox button clicked, this function will run. This function use for autologin, 
		#when clicked, the status of autologin(check or not check) will changed, if autologin 
		#checked, save HOST and PORT, and next show this screen, line edit will auto fill with 
		#the saved value
        global autologin
        autologin = -autologin
        print('autologin = %s'%autologin)
        if autologin ==1:
            self.pBtn_checkbox.setStyleSheet("border-image: url(./images/check2.png);")
        else:
            self.pBtn_checkbox.setStyleSheet("border-image: url(./images/uncheck1.png);")
        print("on_pBtn_checkbox_clicked", HOST, autologin)

class RunningScreen(QtWidgets.QDialog, Ui_Running_screen):
    #Running Screen GUI, inherit from Ui_Running_screen define control functions.
    TIMEOUT = 50
    LEVEL1_SPEED = 50
    LEVEL5_SPEED = 100
    LEVEL2_SPEED = int((LEVEL5_SPEED - LEVEL1_SPEED) / 4 * 1 + LEVEL1_SPEED)#62.5
    LEVEL3_SPEED = int((LEVEL5_SPEED - LEVEL1_SPEED) / 4 * 2 + LEVEL1_SPEED)#75
    LEVEL4_SPEED = int((LEVEL5_SPEED - LEVEL1_SPEED) / 4 * 3 + LEVEL1_SPEED)#87.5
    LEVEL_SPEED = [0, LEVEL1_SPEED, LEVEL2_SPEED, LEVEL3_SPEED, LEVEL4_SPEED, LEVEL5_SPEED]
    
    def __init__(self):
        #Construct screen and set speed top
        QtWidgets.QDialog.__init__(self)
        Ui_Running_screen.__init__(self)
        self.setupUi(self)
        
        self.speed_level = 0
        
        self.level_btn_show(self.speed_level)
        self.setWindowTitle("Operation - SunFounder PiCar-V Client")
        self.btn_back.setStyleSheet("border-image: url(./images/back_unpressed.png);")
        self.btn_setting.setStyleSheet("border-image: url(./images/settings_unpressed.png);")
    
    def start_stream(self):
        # QTimer begins, call refresh_frame to start stream returns pixmap
        self.queryImage = QueryImage(HOST)
        self.timer = QTimer(timeout=self.refresh_frame)  
        self.timer.start(RunningScreen.TIMEOUT) 
        run_action('fwready')
        run_action('bwready')
        run_action('camready')
        
    def stop_stream(self):
        self.timer.stop()
        
    def transToPixmap(self):
        #Convert stream data from camera to pixmap, save queryImage data and create object Pixmap and store data in loadFromData
        data = self.queryImage.queryImage()
        if not data:
            return None
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        return pixmap
    
    def refresh_frame(self):
        #Refresh frame on the widget, use transToPixmap.
        
        pixmap = self.transToPixmap()
        
        if pixmap:
            self.label_snapshot.setPixmap(pixmap)
        else:
            print("frame lost")
    
    def level_btn_show(self, speed_level):
        #change button to pressed or unpressed
        self.level1.setStyleSheet("border-image: url(./images/speed_level_1_unpressed.png);")
        self.level2.setStyleSheet("border-image: url(./images/speed_level_2_unpressed.png);")
        self.level3.setStyleSheet("border-image: url(./images/speed_level_3_unpressed.png);")
        self.level4.setStyleSheet("border-image: url(./images/speed_level_4_unpressed.png);")
        self.level5.setStyleSheet("border-image: url(./images/speed_level_5_unpressed.png);")
        if   speed_level == 1:		# level 1 button is pressed
            self.level1.setStyleSheet("border-image: url(./images/speed_level_1_pressed.png);")
        elif speed_level == 2:		# level 2 button is pressed
            self.level2.setStyleSheet("border-image: url(./images/speed_level_2_pressed.png);")
        elif speed_level == 3:		# level 3 button is pressed
            self.level3.setStyleSheet("border-image: url(./images/speed_level_3_pressed.png);")	
        elif speed_level == 4:		# level 4 button is pressed
            self.level4.setStyleSheet("border-image: url(./images/speed_level_4_pressed.png);")	
        elif speed_level == 5:		# level 5 button is pressed
            self.level5.setStyleSheet("border-image: url(./images/speed_level_5_pressed.png);")	
        
    def set_speed_level(self, speed):
        run_speed(speed)
    
    def keyPressEvent(self, event):
        #Keyboard events
        key_press = event.key()
        if not event.isAutoRepeat():
            if key_press == Qt.Key_Up:
                run_action('camup') 
            elif key_press == Qt.Key_Right:
                run_action('camright')
            elif key_press == Qt.Key_Down:
                run_action('camdown')
            elif key_press == Qt.Key_Left:
                run_action('camleft')
            elif key_press == Qt.Key_W:
                run_action('forward')
            elif key_press == Qt.Key_A:
                run_action('fwleft')
            elif key_press == Qt.Key_S:
                run_action('backward')
            elif key_press == Qt.Key_D:
                run_action('fwright')
            elif key_press == Qt.Key_H:
                run_action('fwstraight')
            elif key_press == Qt.Key_L:
                run_action('speedy')
            elif key_press == Qt.Key_P:
                dubinType(mode,px,py, inrange)
        
    def keyReleaseEvent(self, event):
        key_release = event.key()
        if not event.isAutoRepeat():
            if key_release == Qt.Key_Up:
                run_action('camready')
            elif key_release == Qt.Key_Right:	# right
                run_action('camready')
            elif key_release == Qt.Key_Down:	# down
                run_action('camready')
            elif key_release == Qt.Key_Left:	# left
                run_action('camready')
            elif key_release == Qt.Key_W:		# stop
                run_action('stop')
            elif key_release == Qt.Key_A:		# stop
                run_action('fwstraight')
            elif key_release == Qt.Key_S:		# stop
                run_action('stop')
            elif key_release == Qt.Key_D:		# stop
                run_action('fwstraight')
            
    
    
      
    def on_level1_clicked(self):
        self.speed_level = 1
        self.level_btn_show(self.speed_level)
        self.set_speed_level(str(self.LEVEL_SPEED[self.speed_level]))				
	
    def on_level2_clicked(self):
        self.speed_level = 2
        self.level_btn_show(self.speed_level)
        self.set_speed_level(str(self.LEVEL_SPEED[self.speed_level]))				
	
    def on_level3_clicked(self):
        self.speed_level = 3
        self.level_btn_show(self.speed_level)
        self.set_speed_level(str(self.LEVEL_SPEED[self.speed_level]))			
        
    def on_level4_clicked(self):
        self.speed_level = 4
        self.level_btn_show(self.speed_level)
        self.set_speed_level(str(self.LEVEL_SPEED[self.speed_level]))				
    
    def on_level5_clicked(self):
        self.speed_level = 5
        self.level_btn_show(self.speed_level)
        self.set_speed_level(str(self.LEVEL_SPEED[self.speed_level]))				
        
    def on_btn_back_pressed(self):
        self.btn_back.setStyleSheet("border-image: url(./images/back_pressed.png);")
    def on_btn_back_released(self):
        self.btn_back.setStyleSheet("border-image: url(./images/back_unpressed.png);")
    
    def on_btn_back_clicked(self):
        self.close()
		# close this screen, stop receiving the stream
        self.stop_stream()
        login1.show()
    def on_btn_setting_pressed(self):
        self.btn_setting.setStyleSheet("border-image: url(./images/settings_pressed.png);")
    def on_btn_setting_released(self):
        self.btn_setting.setStyleSheet("border-image: url(./images/settings_unpressed.png);")
    
    def on_btn_setting_clicked(self):
        self.btn_back.setStyleSheet("border-image: url(./images/back_unpressed.png);")
        self.close()
        setting1.show()
        
        
		
class SettingScreen(QtWidgets.QDialog, Ui_Setting_screen):
    
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        Ui_Setting_screen.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("Calibration and Photos")
        self.btn_back.setStyleSheet("border-image: url(./images/back_unpressed.png);")
        self.btn_pics.setStyleSheet("border-image: url (./images/back_unpressed.png);")
    
    def on_btn_camera_cali_pressed(self):
        self.btn_camera_cali.setStyleSheet("border-image: url(./images/camera_cali_pressed.png);")
    def on_btn_camera_cali_released(self):
        self.btn_camera_cali.setStyleSheet("border-image: url(./images/camera_cali_unpressed.png);")
    def on_btn_camera_cali_clicked(self):
        calibrate1.calibration_show(1)
    def on_btn_fw_cali_pressed(self):
        self.btn_fw_cali.setStyleSheet("border-image: url(./images/fw_cali_pressed.png);")
        
    def on_btn_fw_cali_released(self):
        self.btn_fw_cali.setStyleSheet("border-image: url(./images/fw_cali_unpressed.png);")
    def on_btn_fw_cali_clicked(self):
        calibrate1.calibration_show(2)
    def on_btn_bw_cali_pressed(self):
        self.btn_bw_cali.setStyleSheet("border-image: url(./images/bw_cali_pressed.png);")
    def on_btn_bw_cali_released(self):
        self.btn_bw_cali.setStyleSheet("border-image: url(./images/bw_cali_unpressed.png);")
    def on_btn_bw_cali_clicked(self):
        calibrate1.calibration_show(3)
        
    def on_btn_back_pressed(self):
        self.btn_back.setStyleSheet("border-image: url(./images/back_pressed.png);")
    def on_btn_back_released(self):
        self.btn_back.setStyleSheet("border-image: url(./images/back_unpressed.png);")
    def on_btn_back_clicked(self):
        self.close()
        running1.set_speed_level(str(running1.LEVEL_SPEED[running1.speed_level]))				# level 1, speed 20
        running1.show()
    
        
    
    
    
class CalibrateScreen(QtWidgets.QDialog, Ui_Calibrate_screen):
	"""Calibrate Screen

	To create a Graphical User Interface, inherit from Ui_Calibrate_screen. And define functions for the control.

	Attributes:
		none
	"""
	def __init__(self):
		QtWidgets.QDialog.__init__(self)	
		Ui_Calibrate_screen.__init__(self)
		self.setupUi(self)
		self.calibration_status = 0
		self.bw_status = 0

		self.btn_test.setStyleSheet("border-image: url(./images/test_unpressed.png);")
		self.btn_ok.setStyleSheet("border-image: url(./images/ok_unpressed.png);")
		self.btn_cancle.setStyleSheet("border-image: url(./images/cancle_unpressed.png);")

	def calibration_show(self, calibration_status):
		"""Show calibration screen 

		With the argument, show a screen for calibration.argument calibration_status should be 1, 2, or 3, show camera 
		calibration, front wheel calibration and back wheel calibration screen and enter the calibration mode

		Args:
			1, 2, 3, will show camera calibration, front wheel calibration and back wheel calibration screen
		"""
		self.calibration_status = calibration_status	
		if self.calibration_status == 1:				# calibrate camera
			cali_action('camcali')
			self.setWindowTitle("Camera Calibration - SunFounder PiCar-V Client")
			self.label_pic.setStyleSheet("image: url(./images/cali_cam.png);")
			self.label_Cali_Info.setText("Camera")
			self.label_Info_1.setText("Calibrate the camera to the position like above.")
			self.label_Info_2.setText("Use arrow keys or W, A, S, D keys.")
		if self.calibration_status == 2:				# calibrate front wheels
			cali_action('fwcali')
			self.setWindowTitle("Front Wheels Calibration - SunFounder PiCar-V Client")
			self.label_pic.setStyleSheet("image: url(./images/cali_fw.png);")
			self.label_Cali_Info.setText("Front Wheels")
			self.label_Info_1.setText("Calibrate front wheels to the position like above.")
			self.label_Info_2.setText("Use the left and right arrow keys or A and D.")
		if self.calibration_status == 3:				# calibrate back wheels
			cali_action('bwcali')
			run_speed('50')
			run_action('forward')
			self.setWindowTitle("Rear Wheels Calibration - SunFounder PiCar-V Client")
			self.label_pic.setStyleSheet("image: url(./images/cali_bw.png);")
			self.btn_test.hide()
			self.label_Cali_Info.setText("Rear Wheels")
			self.label_Info_1.setText("Calibrate rear wheels to run forward.")
			self.label_Info_2.setText("Use the left and right arrow keys or A and D.")
		self.show()

	def keyPressEvent(self, event):
		"""Keyboard press event

		Press a key on keyboard, the function will get an event, if the condition is met, call the function 
		run_action(). 
		In camera calibration mode, Effective key: W,A,S,D, ↑,  ↓,  ←,  →, ESC
		In front wheel calibration mode, Effective key: A, D, ←,  →, ESC
		In back wheel calibration mode, Effective key: A, D, ←,  →, ESC
		
		Args:
			event, this argument will get when an event of keyboard pressed occured

		"""
		key_press = event.key()

		if key_press in (Qt.Key_Up, Qt.Key_W):    
			if   self.calibration_status == 1:
				cali_action('camcaliup')
			elif self.calibration_status == 2:
				pass
			elif self.calibration_status == 3:
				pass
		elif key_press in (Qt.Key_Right, Qt.Key_D):	
			if   self.calibration_status == 1:
				cali_action('camcaliright')
			elif self.calibration_status == 2:
				cali_action('fwcaliright')
			elif self.calibration_status == 3:
				cali_action('bwcaliright')
		elif key_press in (Qt.Key_Down, Qt.Key_S):	
			if   self.calibration_status == 1:
				cali_action('camcalidown')
			elif self.calibration_status == 2:
				pass
			elif self.calibration_status == 3:
				pass
		elif key_press in (Qt.Key_Left, Qt.Key_A):	
			if   self.calibration_status == 1:
				cali_action('camcalileft')
			elif self.calibration_status == 2:
				cali_action('fwcalileft')
			elif self.calibration_status == 3:
				cali_action('bwcalileft')
				cali_action('forward')
		elif key_press == Qt.Key_Escape:			
			run_action('stop')
			self.close()			

	def on_btn_test_pressed(self):
		self.btn_test.setStyleSheet("border-image: url(./images/test_pressed.png);")
	def on_btn_test_released(self):
		self.btn_test.setStyleSheet("border-image: url(./images/test_unpressed.png);")
		if  self.calibration_status == 1:
			run_action('camup')
			time.sleep(0.5)
			run_action('camready')
			time.sleep(0.5)
			run_action('camdown')
			time.sleep(0.5)
			run_action('camready')
			time.sleep(0.5)
			run_action('camleft')
			time.sleep(0.5)
			run_action('camready')
			time.sleep(0.5)
			run_action('camright')
			time.sleep(0.5)
			run_action('camready')
		elif self.calibration_status == 2:
			run_action('fwleft')
			time.sleep(0.5)
			run_action('fwready')
			time.sleep(0.5)
			run_action('fwright')
			time.sleep(0.5)
			run_action('fwready')
		elif self.calibration_status == 3:
			pass
			
	def on_btn_ok_pressed(self):
		self.btn_ok.setStyleSheet("border-image: url(./images/ok_pressed.png);")
	def on_btn_ok_released(self):
		self.btn_ok.setStyleSheet("border-image: url(./images/ok_unpressed.png);")
	def on_btn_ok_clicked(self):
		# if Ok to calibrate, request to save the value
		if   self.calibration_status == 1:
			cali_action('camcaliok')
		elif self.calibration_status == 2:
			cali_action('fwcaliok')
		elif self.calibration_status == 3:
			cali_action('bwcaliok')
			cali_action('stop')
		self.close()		

	def on_btn_cancle_pressed(self):
		self.btn_cancle.setStyleSheet("border-image: url(./images/cancle_pressed.png);")
	def on_btn_cancle_released(self):
		self.btn_cancle.setStyleSheet("border-image: url(./images/cancle_unpressed.png);")
	def on_btn_cancle_clicked(self):
		# if cancle to calibrate, reset the status
		if   self.calibration_status == 1:
			run_action('camready')
		elif self.calibration_status == 2:
			run_action('fwready')
		elif self.calibration_status == 3:
			run_action('bwready')
			cali_action('stop')
		self.close()		

class QueryImage:
	"""Query Image
	
	Query images form http. eg: queryImage = QueryImage(HOST)

	Attributes:
		host, port. Port default 8080, post need to set when creat a new object

	"""
	def __init__(self, host, port=8080, argv="/?action=snapshot"):
		# default port 8080, the same as mjpg-streamer server
		self.host = host
		self.port = port
		self.argv = argv
	
	def queryImage(self):
		"""Query Image

		Query images form http.eg:data = queryImage.queryImage()

		Args:
			None

		Return:
			returnmsg.read(), http response data
		"""
		http_data = http.client.HTTPConnection(self.host, self.port)
		http_data.putrequest('GET', self.argv)
		http_data.putheader('Host', self.host)
		http_data.putheader('User-agent', 'python-http.client')
		http_data.putheader('Content-type', 'image/jpeg')
		http_data.endheaders()
		returnmsg = http_data.getresponse()

		return returnmsg.read()


def connection_ok():
	"""Check whether connection is ok

	Post a request to server, if connection ok, server will return http response 'ok' 

	Args:
		none

	Returns:
		if connection ok, return True
		if connection not ok, return False
	
	Raises:
		none
	"""
	cmd = 'connection_test'
	url = BASE_URL + cmd + "/"
	print('url: %s'% url)
	# if server find there is 'connection_test' in request url, server will response 'Ok'
	try:
		r=requests.get(url)
		if r.text == 'OK':
			return True
	except:
		return False

def __request__(url, times=10):
	for x in range(times):
		try:
			requests.get(url)
			return 0
		except :
			print("Connection error, try again")
	print("Abort")
	return -1

def run_action(cmd):
	"""Ask server to do cmd, use in running mode

	Post requests to server, server will do what client want to do according to the url.
	This function for running mode

	Args:
		# ============== Back wheels =============
		'bwcali' | 'bwcalileft' | 'bwcaliright' | 'bwcaliok' 

		# ============== Front wheels =============
		'fwcali' | 'fwcalileft' | 'fwcaliright' |  'fwcaliok'
        
        # ============== Turning Circles =============
		'Rturn' | 'Lturn' | 'left_circle' |  'right_circle' | 'speedy' | 'slowy' | 'reverse' 

		# ================ Camera =================
		'camcali' | 'camcaliup' | 'camcalidown' | 'camcalileft' | 'camright' | 'camcaliok' 
	"""
	# set the url include action information
	url = BASE_URL + 'run/?action=' + cmd
	print('url: %s'% url)
	# post request with url 
	__request__(url)

def run_speed(speed):
	"""Ask server to set speed, use in running mode

	Post requests to server, server will set speed according to the url.
	This function is for running mode.

	Args:
		'0'~'100'
	"""
	# Set set-speed url
	url = BASE_URL + 'run/?speed=' + speed
	print('url: %s'% url)
	# Set speed
	__request__(url)

def cali_action(cmd):
	"""Ask server to do cmd, use in calibration mode

	Post requests to server, server will do what client want to do according to the url.
	This function for calibration mode

	Args:
		# ============== Back wheels =============
		'bwcali' | 'bwcalileft' | 'bwcaliright' | 'bwcaliok' 

		# ============== Front wheels =============
		'fwcali' | 'fwcalileft' | 'fwcaliright' |  'fwcaliok'
        
        # ============== Turning Circles =============
		'Rturn' | 'Lturn' | 'left_circle' |  'right_circle' | 'speedy' | 'slowy' | 'reverse' 

		# ================ Camera =================
		'camcali' | 'camcaliup' | 'camcalidown' | 'camcalileft' | 'camright' | 'camcaliok' 

	"""
	# set the url include cali information
	url = BASE_URL + 'cali/?action=' + cmd
	print('url: %s'% url)
	# post request with url 
	__request__(url)


def checker1(inrange):
    for i in range(len(inrange)):
        if inrange[i] ==1:
            return i
    
    
def checker2(inrange):
    j = np.argmax(inrange)
    print(j)
    return j
            
def checker3(inrange):
  k = len(inrange)-2
  return k
    
    
def distancefirstcircle(px,py,i):
    distance = math.sqrt((px[i]-px[0])**2 + (py[i]-py[0])**2)
    speed = 0.266616
    gofor = distance/speed
    gofor = gofor/2 #semi cirlce not full
    
    return gofor

    
def distanceStraight(px,py,i,j):
    distance = math.sqrt((px[j]-px[i])**2 + (py[j]-py[i])**2)
    speed = 0.493815
    gofor2 = distance/speed
    
    return gofor2
    
def distancelastCircle(px,py,j,k):
    distance = math.sqrt((px[k]-px[j])**2 + (py[k]-py[j])**2)#1.9962088955494706
    speed = 0.266616
    gofor3 = distance/speed
    gofor3 = gofor3/2 #semi cirlce not full
    
    return gofor3


def dubinType(mode,px,py,inrange):

    all_zeros = not np.any(inrange)
    if all_zeros == True:
        print("Try a different point in Dubins_path_planning file")
	
    x = distancefirstcircle(px,py,i)
    y = distanceStraight(px,py,i,j)
    z = distancelastCircle(px,py,j,k)
    if mode == ['R','S','R']:
        start = time.time()
        run_action('right_circle')
        time.sleep(x)
        run_action('fwstraight')
        run_action('speedy')
        time.sleep(y)
        run_action('slowy')
        run_action('right_circle')
        time.sleep(z)
        run_action('fwstraight')
        stop = time.time()
        run_action('stop')
        timerun = stop-start
        print("I took {} seconds".format(timerun))
    elif mode == ['R','S','L']:
        start = time.time()
        run_action('right_circle')
        time.sleep(x)
        run_action('fwstraight')
        run_action('speedy')
        time.sleep(y)
        run_action('slowy')
        run_action('left_circle')
        time.sleep(z)
        run_action('fwstraight')
        stop = time.time()
        run_action('stop')
        timerun = stop-start
        print("I took {} seconds".format(timerun))
    elif mode == ['L','S','R']:
        start = time.time()
        run_action('left_circle')
        time.sleep(x)
        run_action('fwstraight')
        run_action('speedy')
        time.sleep(y)
        run_action('slowy')
        run_action('right_circle')
        time.sleep(z)
        run_action('fwstraight')
        stop = time.time()
        timerun = stop-start
        print("I took {} seconds".format(timerun))
    elif mode == ['L','S','L']:
        start = time.time()
        run_action('left_circle')
        time.sleep(x)
        run_action('fwstraight')
        run_action('speedy')
        time.sleep(y)
        run_action('slowy')
        run_action('left_circle')
        time.sleep(z)
        run_action('fwstraight')
        stop = time.time()
        run_action('stop')
        timerun = stop-start
        print("I took {} seconds".format(timerun))
        
    reverse(mode,x,y,z)
    
    distance_travelled1 = x * 0.266616 #time x * speed
    distance_travelled2 = y * 0.493815 #time y * speed
    distance_travelled3 = z * 0.266616 #time z * speed
    
    dis_total = distance_travelled1 + distance_travelled2 + distance_travelled3 
    
    average_speed = dis_total/timerun
    
    rps = average_speed / 0.398982 #average speed/ circumference of seed dispsenser
    print("RPS = {}".format(rps))
    
 
def reverse(mode,x,y,z):
    #inverse of Dubins path
    if mode == ['R','S','R']:
        start = time.time()
        run_action('Lturn')
        time.sleep(x)
        run_action('fwstraight')
        run_action('reverse')
        time.sleep(y)
        run_action('slowy')
        run_action('Lturn')
        time.sleep(z)
        run_action('fwstraight')
        stop = time.time()
        run_action('stop')
        timerun = stop-start
        print("I took {} seconds".format(timerun))
    elif mode == ['R','S','L']:
        start = time.time()
        run_action('Lturn')
        time.sleep(x)
        run_action('fwstraight')
        run_action('reverse')
        time.sleep(y)
        run_action('slowy')
        run_action('Rturn')
        time.sleep(z)
        run_action('fwstraight')
        stop = time.time()
        run_action('stop')
        timerun = stop-start
        print("I took {} seconds".format(timerun))
    elif mode == ['L','S','R']:
        start = time.time()
        run_action('Rturn')
        time.sleep(x)
        run_action('fwstraight')
        run_action('reverse')
        time.sleep(y)
        run_action('slowy')
        run_action('Lturn')
        time.sleep(z)
        run_action('fwstraight')
        stop = time.time()
        run_action('stop')
        timerun = stop-start
        print("I took {} seconds".format(timerun))
    elif mode == ['L','S','L']:
        start = time.time()
        run_action('Rturn')
        time.sleep(x)
        run_action('fwstraight')
        run_action('reverse')
        time.sleep(y)
        run_action('slowy')
        run_action('Rturn')
        time.sleep(z)
        run_action('fwstraight')
        stop = time.time()
        run_action('stop')
        timerun = stop-start
        print("I took {} seconds".format(timerun))
        


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    #Create Objects
    login1 = LoginScreen()
    running1 = RunningScreen()
    setting1 = SettingScreen()
    calibrate1 = CalibrateScreen()
    login1.show()
    mode,px,py,inrange = dubins.main()
    i=checker1(inrange)
    j=checker2(inrange)
    k =checker3(inrange)
    
    print("Online")
    sys.exit(app.exec_())
