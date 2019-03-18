import serial
from pythonosc import osc_message_builder
from pythonosc import udp_client


serialPort = serial.Serial("/dev/ttyUSB0", baudrate=9600)

sendAddress= '192.168.0.13'
port = 9001
client = udp_client.SimpleUDPClient(sendAddress,port)
msg = "/blender/1"

while True:
    cc=str(serialPort.readline())
    dist = (cc[2:][:-5])
    print (dist)
    intDist = int(dist)
    client.send_message(msg,intDist)
