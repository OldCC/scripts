import sys
import serial
import math
import operator
import time
import socket

GPS_IP = "127.0.0.3"
GPS_PORT = 5005

t_gps = time.time()
t_fail = 0

ser = serial.Serial('/dev/ttyUSB1', 4800, timeout=1)

while True:

    hack = time.time()
    gps_raw = ser.readline()
    if "*" in gps_raw:
        gps_split = gps_raw.split('*')
        gps_sentence = gps_split[0].strip('$')
        cs0 = gps_split[1][:-2]
        cs1 = format(reduce(operator.xor,map(ord,gps_sentence),0),'X')
        if len(cs1) == 1:
            cs1 = "0" + cs1
        if cs0 == cs1:

            gps_vars = gps_sentence.split(',')
            title = gps_vars[0]

            if title == "GPRMC":
                t_gps = hack
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(gps_raw, (GPS_IP, GPS_PORT))

    if (hack - t_gps) > 10.0:
        gps_sentence = "$IIXDR,GPS_FAIL*7B"
        #print gps_sentence
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(gps_sentence, (GPS_IP, GPS_PORT))
        t_fail += 1
        t_gps = hack
        if t_fail > 29:
            sys.exit(1)
