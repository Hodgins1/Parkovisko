
from flask import *								# FLASK - webovy aplikacny framework
import time										# kniznica na pracu s casom
import smbus
from flask_socketio import SocketIO				# Socket.IO - komunikacia kleint-server v realnom case
import eventlet
import serial
import MPR121 as CK
import Display_I2C as DS
import RPi.GPIO as GPIO

# Get I2C bus
bus = smbus.SMBus(1)
TEMP_sensor = 0x45

TEMP = "n/a"
HUM = "n/a"
FUN = 1250
MAX_car = 20
ACTUAL_car = 0
STATE = 0

password = '1111'
test_psw = ''

eventlet.monkey_patch()							# inicializovanie sietovej kniznice
app = Flask(__name__)							# vytvorenie instancie triedy pre Flask									# vytvorenie instancie triedy pre kotolu stavu kamier a obrazoviek
socketio = SocketIO(app)						# vytvorenie instancie triedy SocketIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
RAMPA = 21
ODCHOD = 20
GPIO.setup(RAMPA, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(ODCHOD, GPIO.IN)

ser = serial.Serial(
		port='/dev/ttyAMA0',
		baudrate=9600,
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		bytesize=serial.EIGHTBITS,
		timeout=1
	)

@socketio.on('refresh')							# cakanie pripojenie kleinta a nasledne odoslanie stavu vsetkych kamier
def prveSpojenie1(msg):
	print(msg)									# vypis na konzolu ze sa prihlasil novy uzivatel

@app.route("/")									# previazanie URL adresy s funkciou
def index():
	return render_template('index.html')		# generovanie HTML suboru

def SENSORS_REFRESH():								# funkcia pre kontrolu zmenu stavu kamery
	global TEMP, HUM
	while True:
		bus.write_i2c_block_data(TEMP_sensor, 0x2C, [0x06])
		eventlet.sleep(2)
		data = bus.read_i2c_block_data(TEMP_sensor, 0x00, 6)
		TEMP = round(((((data[0] * 256.0) + data[1]) * 175) / 65535.0) - 45,2)
		HUM = round(100 * (data[3] * 256 + data[4]) / 65535.0,1)


def Bluetooth():
	while True:
		if (ser.inWaiting() > 0):
			x = ser.readline()
			print (x)
		eventlet.sleep(0.1)

def TEST():
	global ACTUAL_car
	while True:
		ACTUAL_car = ACTUAL_car + 1
		if ACTUAL_car == MAX_car:
			ACTUAL_car = 0
		eventlet.sleep(5)

def WEB_REFRESH():
	while True:
		socketio.emit('Ventilator', {'value':FUN})
		socketio.emit('Auta', {'act': ACTUAL_car, 'max': MAX_car})	#odoslanie noveho stavu kamery
		socketio.emit('Teplota', {'value':TEMP})	#odoslanie noveho stavu kamery
		socketio.emit('Vlhkost', {'value': HUM})	#odoslanie noveho stavu kamery
		eventlet.sleep(2)

def CONSOLE_REFRESH():
	while True:
		print 'Ventilator: ', FUN, ' RPM'
		print 'Pocet aut: ', ACTUAL_car, '/' , MAX_car		# vypisanie noveho stavu kamery na konzolu
		print 'Vlhkost: ', HUM , '%'		# vypisanie noveho stavu kamery na konzolu
		print 'Teplota: ', TEMP, ' C' 		    # vypisanie noveho stavu kamery na konzolu
		print '------------------------------------'
		eventlet.sleep(2)

def Button():
	global ACTUAL_car
	while True:
		if (GPIO.input(ODCHOD))==0 and ACTUAL_car !=0:
			ACTUAL_car = ACTUAL_car - 1

		eventlet.sleep(0.5)

def TouchPad():
	global STATE, test_psw,password
	CK.setup(0x5a)
	last_touched = CK.readData(0x5a)
	lastTap = 0

	while True:
		data = CK.readData(0x5a)
		if(data != 0 and data != lastTap): #testuje sa ci bolo stlacene nieco nove
			eventlet.sleep(0.05)
			if (STATE == 0 and data == 8):
				STATE = 1
			elif(STATE == 1):
				if(data == 1):
					test_psw = test_psw + "3"
				elif(data == 2):
					test_psw = test_psw + "6"
				elif(data == 4):
					test_psw = test_psw + "9"
				elif(data == 8):
					STATE = 2
				elif(data == 16):
					test_psw = test_psw + "2"
				elif(data == 32):
					test_psw = test_psw + "5"
				elif(data == 64):
					test_psw = test_psw + "8"
				elif(data == 128):
					test_psw = test_psw + "0"
				elif(data == 256):
					test_psw = test_psw + "1"
				elif(data == 512):
					test_psw = test_psw + "4"
				elif(data == 1024):
					test_psw = test_psw + "7"
				elif(data == 2048):
					if len(test_psw) == 0 :
						STATE = 0
					else:
						test_psw = test_psw[:-1]
		lastTap = data
		eventlet.sleep(0.05)

def Display():
	DS.lcd_init()
	global test_psw, STATE, ACTUAL_car
	PAR = 0
	while True:
		if STATE == 0:
			DS.lcd_string( "   PARKOVISKO",DS.LCD_LINE_1)
			DS.lcd_string( "Pocet aut: " +str(ACTUAL_car) + "/" + str(MAX_car),DS.LCD_LINE_2)
		if STATE == 1:
			DS.lcd_string( "Lokalny vstup",DS.LCD_LINE_1)
			DS.lcd_string( "PIN:" +  test_psw,DS.LCD_LINE_2)
		if STATE == 2:
			print test_psw
			if test_psw == password:
				if ACTUAL_car == MAX_car:
					DS.lcd_string( "PLNE  PARKOVISKO",DS.LCD_LINE_1)
					DS.lcd_string( " Pridte  neskor ",DS.LCD_LINE_2)
				else:
					GPIO.output(21, GPIO.HIGH)
					DS.lcd_string( "  Heslo prijate ",DS.LCD_LINE_1)
					DS.lcd_string( "    Vitajte     ",DS.LCD_LINE_2)
					ACTUAL_car = ACTUAL_car + 1
			else:
				DS.lcd_string( "   ZAMIETNUTE   ",DS.LCD_LINE_1)
				DS.lcd_string( " zadajte  znova ",DS.LCD_LINE_2)
			eventlet.sleep(2)
			GPIO.output(21, GPIO.LOW)
			test_psw = ''
			STATE = 0

		if STATE == 9:
			DS.lcd_string( "Neplatny znak !!",DS.LCD_LINE_2)

		eventlet.sleep(0.2)




if __name__ == "__main__":
	print "Press Ctrl C to end"
	eventlet.spawn(TouchPad)
	eventlet.spawn(SENSORS_REFRESH)
	eventlet.spawn(Button)
	# eventlet.spawn(TEST)
	eventlet.spawn(Display)
	eventlet.spawn(WEB_REFRESH)
	eventlet.spawn(CONSOLE_REFRESH)
					# vytvorenie vlakna pre kontolu stavu kamery
	socketio.run(app, host='0.0.0.0', debug=False) # start weboheho servera
