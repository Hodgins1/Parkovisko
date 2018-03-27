import serial

ser = serial.Serial(

    port='/dev/ttyS0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)
counter = 0

while 1:

    if ser.inWaiting() > 0:
        x = ser.readline()
        print (x)



        
def Button():								# funkcia pre kontrolu zmenu stavu kamery
   CK.setup(0x5a)
   last_touched = readData(0x5a)
   lastTap = 0
   while True:
	data = readData(0x5a)
	if(data != 0 and data != lastTap): #testuje sa ci bolo stlacene nieco nove
	    print (data)

	    lastTap = data
	eventlet.sleep(0.01)
