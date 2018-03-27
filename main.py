
from flask import *								# FLASK - webovy aplikacny framework
import time										# kniznica na pracu s casom
import smbus
from flask_socketio import SocketIO				# Socket.IO - komunikacia kleint-server v realnom case
import eventlet
import serial
import MPR121 as CK

# Get I2C bus
bus = smbus.SMBus(1)
TEMP_sensor = 0x45

MAX_car = 20
ACTUAL_car = 0
STATE = 0

eventlet.monkey_patch()							# inicializovanie sietovej kniznice
app = Flask(__name__)							# vytvorenie instancie triedy pre Flask									# vytvorenie instancie triedy pre kotolu stavu kamier a obrazoviek
socketio = SocketIO(app)						# vytvorenie instancie triedy SocketIO

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

def Temperature():								# funkcia pre kontrolu zmenu stavu kamery
	while True:
		bus.write_i2c_block_data(TEMP_sensor, 0x2C, [0x06])
		eventlet.sleep(3)
		data = bus.read_i2c_block_data(TEMP_sensor, 0x00, 6)
		cTemp = round(((((data[0] * 256.0) + data[1]) * 175) / 65535.0) - 45,2)
		humidity = round(100 * (data[3] * 256 + data[4]) / 65535.0,1)
		socketio.emit('Teplota', {'value':cTemp})	#odoslanie noveho stavu kamery
		print 'Teplota: ', cTemp, ' C' 		    # vypisanie noveho stavu kamery na konzolu
		socketio.emit('Vlhkost', {'value': humidity})	#odoslanie noveho stavu kamery
		print 'Vlhkost: ', humidity , '%'		# vypisanie noveho stavu kamery na konzolu
		print '------------------------------------'

def Display():
	print "Inicializacia displeja"
	while True:
		if STATE == 0:
			print "1: PARKOVISKO"
			print "2: Pocet aut: ", ACTUAL_car,"/",MAX_car

		if STATE == 1:
			print "1: Zadaj PIN:"
			print "2: "

		if STATE == 2:
			print "TODO"

		eventlet.sleep(0.5)

def Bluetooth():
	while True:
		if (ser.inWaiting() > 0):
			x = ser.readline()
			print (x)
		print("ahoj")
		eventlet.sleep(0.1)

def Button():
	CK.setup(0x5a)
	last_touched = CK.readData(0x5a)
	lastTap = 0
	pasw = ''
	while True:
		data = CK.readData(0x5a)
		if(data != 0 and data != lastTap): #testuje sa ci bolo stlacene nieco nove
			eventlet.sleep(0.05)
			print(data)
			# if (STATE == 0 and data == 8):
			# 	STATE = 1
			# if(STATE == 1 and data != 2048):
			# 	if(data == 8):
			# 		print (data)
			lastTap = data
		eventlet.sleep(0.05)




if __name__ == "__main__":
	print "Press Ctrl C to end"
	eventlet.spawn(Button)
	#eventlet.spawn(Bluetooth)
	#eventlet.spawn(Display)
	eventlet.spawn(Temperature)					# vytvorenie vlakna pre kontolu stavu kamery
	socketio.run(app, host='0.0.0.0', debug=False) # start weboheho servera
