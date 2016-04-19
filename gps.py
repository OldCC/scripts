import sys
import serial
import math
import operator
import time
import socket
import os

GPS_IP = "127.0.0.1"
GPS_PORT = 5005

MON_IP = "127.0.0.4"
MON_PORT = 5005

mon = 0
log = time.time()

# determine gps port
f = open('gps_port', 'r')
gps_port = f.readline()
f.close()
ser = serial.Serial('/dev/ttyUSB' + gps_port, 4800, timeout=5)

while True:

    # health monitor
    hack = time.time()
    if hack - mon > .5:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(str(hack), (MON_IP, MON_PORT))
        mon = hack

    # log raw input
    gps_raw = ser.readline()
    f = open('gpsraw', 'a')
    f.write(gps_raw)
    f.close()
    if hack - log > 60:
        os.remove('gpsraw')
        f = open('gpsraw', 'w')
        f.write("Serial port " + gps_port + ": " + time.asctime( time.localtime(time.time()) ) + "\r\n")
        f.close()
        log = hack

    # checking to see if it's a valid NMEA sentence
    if "*" in gps_raw:
        gps_split = gps_raw.split('*')
        gps_sentence = gps_split[0].strip('$')
        cs0 = gps_split[1][:-2]
        cs1 = format(reduce(operator.xor,map(ord,gps_sentence),0),'X')
        if len(cs1) == 1:
            cs1 = "0" + cs1

        # if it is a valid NMEA sentence
        if cs0 == cs1:
            gps_vars = gps_sentence.split(',')
            title = gps_vars[0]

            # recommended minimum navigation sentence
            if title == "GPRMC":

                # heading from IMU
                try:
                    f = open('imu_bus', 'r')
                    line = f.readline()
                    f.close()
                    imu_split = line.split(',')
                    imu_hack = float(imu_split[0])
                    heading = float(imu_split[1])    
                except ValueError:
                    f.close()
                    time.sleep(.03)
                    f = open('imu_bus', 'r')
                    line = f.readline()
                    f.close()
                    imu_split = line.split(',')
                    imu_hack = float(imu_split[0])
                    heading = float(imu_split[1])

                # if heading is from the last 3 seconds, and groundspeed less than .1,
                # reset course to heading to eliminate low speed artifacts
                valid = gps_vars[2]
                course = float(gps_vars[8])
                groundspeed = float(gps_vars[7])
                if time.time() - imu_hack < 3.0 and groundspeed < 0.1:
                    course = heading

                # assemble the sentence with corrected course
                rmc = "GPRMC," + gps_vars[1] + ',' + gps_vars[2] + ',' + gps_vars[3] + ',' + gps_vars[4] + ',' + gps_vars[5] + ',' + gps_vars[6] + ',' + str(groundspeed) + ',' + str(int(round(course))) + ',' + gps_vars[9] + ',,'
                rmccs = format(reduce(operator.xor,map(ord,rmc),0),'X')
                if len(rmccs) == 1:
                        rmccs = "0" + rmccs
                gprmc = "$" + rmc + "*" + rmccs + "\r\n"

                # to gps bus
                f = open('gps_bus', 'w')
                f.write(str(time.time()) + ',' + valid + ',' + str(course)  + ',' + str(groundspeed))
                f.close()

                # to kplex
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(gprmc, (GPS_IP, GPS_PORT))
