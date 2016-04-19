#!/usr/bin/env python

import serial
import operator
import time
import os
import sys
import socket
import select

# change the working directory to the scripts folder
os.chdir("home/pi/kts/scripts")

# log
hack = time.asctime( time.localtime(time.time()) )
log = open('log', 'w')
log.write("Monitor initialized: " + str(hack) + "\r\n")
log.close()

# determine GPS/DST ports
init = 0
while init == 0:

    # check port 0
    port0 = serial.Serial('/dev/ttyUSB0', 4800, timeout=3)
    port0_raw = port0.readline()
    hack = time.asctime( time.localtime(time.time()) )
    log = open('log', 'a')
    log.write("Checking serial port 0: " + str(hack) + "\r\n")
    log.close()
    if "*" in port0_raw:
        port0_split = port0_raw.split('*')
        port0_sentence = port0_split[0].strip('$')
        cs0 = port0_split[1][:-2]
        cs1 = format(reduce(operator.xor,map(ord,port0_sentence),0),'X')
        if len(cs1) == 1:
            cs1 = "0" + cs1

        # if it is a valid NMEA sentence
        if cs0 == cs1:
            port0_vars = port0_sentence.split(',')
            title = port0_vars[0]

            # if the GPS is connected to this port
            if title == "GPRMC":
                gps = "0"
                f = open('gps_port', 'w')
                f.write(gps)
                f.close()
                init = 1

            # if the DST is connected to this port
            if title == "SDDPT":
                gps = "1"
                f = open('gps_port', 'w')
                f.write(gps)
                f.close()
                init = 1
    port0.close()

    # check port 1
    port1 = serial.Serial('/dev/ttyUSB1', 4800, timeout=3)
    port1_raw = port1.readline()
    hack = time.asctime( time.localtime(time.time()) )
    log = open('log', 'a')
    log.write("Checking serial port 1: " + str(hack) + "\r\n")
    log.close()
    if "*" in port1_raw:
        port1_split = port1_raw.split('*')
        port1_sentence = port1_split[0].strip('$')
        cs0 = port1_split[1][:-2]
        cs1 = format(reduce(operator.xor,map(ord,port1_sentence),0),'X')
        if len(cs1) == 1:
            cs1 = "0" + cs1

        # if it is a valid NMEA sentence
        if cs0 == cs1:
            port1_vars = port1_sentence.split(',')
            title = port1_vars[0]

            # if the GPS is connected to this port
            if title == "GPRMC":
                gps = "1"
                f = open('gps_port', 'w')
                f.write(gps)
                f.close()
                init = 1

            # if the DST is connected to this port
            if title == "SDDPT":
                gps = "0"
                f = open('gps_port', 'w')
                f.write(gps)
                f.close()
                init = 1
    port1.close()

log = open('log', 'a')
log.write("GPS port is " + gps + ": " + str(hack) + "\r\n")
log.close()

# begin the instrument scripts
hack = time.asctime( time.localtime(time.time()) )
log = open('log', 'a')
log.write("Starting gps: " + str(hack) + "\r\n")
log.close()
os.system("python gps.py &")
hack = time.asctime( time.localtime(time.time()) )
log = open('log', 'a')
log.write("Starting imu: " + str(hack) + "\r\n")
log.close()
os.system("python imu.py &")
hack = time.asctime( time.localtime(time.time()) )
log = open('log', 'a')
log.write("Starting dst: " + str(hack) + "\r\n")
log.close()
os.system("python dst.py &")
hack = time.asctime( time.localtime(time.time()) )
log = open('log', 'a')
log.write("Starting kplex: " + str(hack) + "\r\n")
log.close()
os.system("sudo kplex &")

GPS_IP = "127.0.0.4"
GPS_PORT = 5005
gpssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
gpssock.bind((GPS_IP, GPS_PORT))

IMU_IP = "127.0.0.5"
IMU_PORT = 5005
imusock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
imusock.bind((IMU_IP, IMU_PORT))

DST_IP = "127.0.0.6"
DST_PORT = 5005
dstsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dstsock.bind((DST_IP, DST_PORT))

hack = time.asctime( time.localtime(time.time()) )
log = open('log', 'a')
log.write("Starting loop: " + str(hack) + "\r\n" + "------------------------\r\n")
log.close()

gps_hack = time.time()
imu_hack = time.time()
dst_hack = time.time()
while True:

    # monitor gps.py
    gpsready = select.select([gpssock], [], [], .1)
    if gpsready [0]:
        data, addr = gpssock.recvfrom(1024)
        gps_hack = float(data)
    if time.time() - gps_hack > 10.0:
        hack = time.asctime( time.localtime(time.time()) )
        log = open('log', 'a')
        log.write("Restarting gps: " + str(hack) + "\r\n")
        log.close()
        os.system("pkill -9 -f gps.py")
        os.system("python gps.py &")
        gps_hack = time.time()
        

    # monitor imu.py
    imuready = select.select([imusock], [], [], .1)
    if imuready [0]:
        data, addr = imusock.recvfrom(1024)
        imu_hack = float(data)
    if time.time() - imu_hack > 10.0:
        hack = time.asctime( time.localtime(time.time()) )
        log = open('log', 'a')
        log.write("Restarting imu: " + str(hack) + "\r\n")
        log.close()
        os.system("pkill -9 -f imu.py")
        os.system("python imu.py &")
        imu_hack = time.time()

    # monitor dst.py
    dstready = select.select([dstsock], [], [], .1)
    if dstready [0]:
        data, addr = dstsock.recvfrom(1024)
        dst_hack = float(data)
    if time.time() - dst_hack > 10.0:
        hack = time.asctime( time.localtime(time.time()) )
        log = open('log', 'a')
        log.write("Restarting dst: " + str(hack) + "\r\n")
        log.close()
        os.system("pkill -9 -f dst.py")
        os.system("python dst.py &")
        dst_hack = time.time()
