import sys
import serial
import math
import operator
import time
import socket

DST_IP = "127.0.0.4"
DST_PORT = 5005

vlwfirst = 1
vlwinit = 0.0
t_dpt = 0
t_print = time.time()
t_fail = 0.0

sddpt = ''
mtw = ''
yxmtw = ''
vwvhw = ''
vlw = ''
vwvlw = ''

ser = serial.Serial('/dev/ttyUSB0', 4800, timeout=1)

while True:
    hack = time.time()

    dst_raw = ser.readline()

    if "*" in dst_raw:
        dst_split = dst_raw.split('*')
        dst_sentence = dst_split[0].strip('$')
        cs0 = dst_split[1][:-2]
        cs = format(reduce(operator.xor,map(ord,dst_sentence),0),'X')
        if len(cs) == 1:
            cs = "0" + cs

        if cs0 == cs:

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            dst_vars = dst_sentence.split(',')
            title = dst_vars[0]

            if title == "SDDPT":
                sddpt = dst_raw[:-2]
                sock.sendto(sddpt, (DST_IP, DST_PORT))
                t_dpt = hack
                t_fail = 0.0

            if title == "YXMTW":
                mtw = dst_vars[0] + "," + str(float(dst_vars[1]) * 9 / 5 + 32) + ",F"
                cs = format(reduce(operator.xor,map(ord,mtw),0),'X')
                if len(cs) == 1:
                    cs = "0" + cs
                yxmtw = "$" + mtw + "*" + cs
                sock.sendto(yxmtw, (DST_IP, DST_PORT))

            if title == "VWVHW":
                vwvhw = dst_raw[:-2]
                sock.sendto(vwvhw, (DST_IP, DST_PORT))

            if title == "VWVLW":
                if vlwfirst == 1:
                    vlwinit = dst_vars[1]
                    vlwfirst = 0
                trip = float(dst_vars[1]) - float(vlwinit)
                vlw = "VWVLW," + dst_vars[1] + ",N," + str(trip) + ",N"
                cs = format(reduce(operator.xor,map(ord,mtw),0),'X')
                if len(cs) == 1:
                    cs = "0" + cs
                vwvlw = "$" + vlw + "*" + cs
                sock.sendto(vwvlw, (DST_IP, DST_PORT))

    if (hack - t_dpt) > 10.0:
        if (hack - t_print > 1.0):
            t_fail += 1.0
            dst_sentence = "IIXDR,DST_FAIL," + str(round(t_fail / 60, 1))
            cs = format(reduce(operator.xor,map(ord,dst_sentence),0),'X')
            if len(cs) == 1:
                cs = "0" + cs
            dst_sentence = "$" + dst_sentence + "*" + cs
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(dst_sentence, (DST_IP, DST_PORT))
            t_print = hack
