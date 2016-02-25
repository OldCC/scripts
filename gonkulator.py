import serial
import math
import operator
import time
import socket
import select
import os

GONK_IP = "127.0.0.5"
GONK_PORT = 5005

IMU_IP = "127.0.0.2"
IMU_PORT = 5005
imusock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
imusock.bind((IMU_IP, IMU_PORT))

GPS_IP = "127.0.0.3"
GPS_PORT = 5005
gpssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
gpssock.bind((GPS_IP, GPS_PORT))

DST_IP = "127.0.0.4"
DST_PORT = 5005
dstsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dstsock.bind((DST_IP, DST_PORT))

roll = 0.0
pitch = 0.0
heading = 0
waterspeed = 0.0
course = 0
groundspeed = 0.0
set_true = 0
drift = 0.0

# timers
t_print = time.time()
t_imu = time.time()
t_gps = time.time()
t_dst = time.time()
t_vhw = time.time()
t_imu_restart = 0
t_gps_restart = 0
t_dst_restart = 0

# blank sentences
iihdt0 = "$IIHDT,,T*0C"
iixdr0 = "$IIXDR,A,,D,ROLL,A,,D,PTCH,A,,D,RLLR,A,,D,PTCR,A,,D,YAWR*51"
gprmc0 = "$GPRMC,,V,,N,,W,,,,,*28"
sddpt0 = "$SDDPT,,0.50*4C"
sddpt0 = "$SDDPT,,0.50*4C"
yxmtw0 = "$YXMTW,,F*09"
vwvhw0 = "$VWVHW,,T,,M,,N,,K*54"
vwvlw0 = "$VWVLW,,N,,N*53"
iivdr0 = "$IIVDR,A,,T,,R,,N*65"

# initialize sentences
iihdt = ''
iixdr = ''
gprmc = ''
sddpt = ''
yxmtw = ''
vwvhw = ''
vwvlw = ''
iivdr = ''
imusentence = ''
gpssentence = ''
dstsentence = ''
vdrsentence = ''

# data drops
imu_init_fail = 0
imu_init_drop = 0
imu_fail_drop = 0
imu_timeout_drop = 0
gpsdrop = 0
gps_timeout_drop = 0
dstdrop = 0
dst_timeout_drop = 0

# VDR
imufail = 1
gpsfail = 1
vhwfail = 1
vdrfail = 1
t_ten = 0
setx_total = 0
setx_run = [0] * 10
sety_total = 0
sety_run = [0] * 10
drift_total = 0
drift_run = [0] * 10

while True:
    
    hack = time.time()

    ##### MPU-9250 IMU #####
    imuready = select.select([imusock], [], [], .1)
    if imuready[0]:
        t_imu = hack
        data, addr = imusock.recvfrom(1024)

        if data == "$IIXDR,IMU_FAILED_TO_INITIALIZE*7C":
            imu_init_fail = 1
            imu_fail_drop = 0
            imu_timeout_drop = 0
            imufail = 1
            if imu_init_drop == 0:
                imusentence = iihdt0 + '\r\n' + iixdr0
                imu_init_drop = 1
            else: imusentence = data
        elif data == "$IIXDR,IMU_FAIL*6E":
            imu_init_fail = 0
            imu_init_drop = 0
            imu_timeout_drop = 0
            imufail = 1
            if imu_fail_drop == 0:
                imusentence = iihdt0 + '\r\n' + iixdr0
                imu_fail_drop = 1
            else: imusentence = data
        else:
            imu_init_fail = 0
            imu_init_drop = 0
            imufail = 0
            imu_fail_drop = 0
            imu_timeout_drop = 0
            imuvars = data.split(',')
            heading = float(imuvars[1])
            roll = float(imuvars[4])
            pitch = float(imuvars[8])
            imusentence = data   
    
    if (hack - t_imu) > 10.0:
        imufail = 1
        if imu_timeout_drop == 0:
            imusentence = iihdt0 + '\r\n' + iixdr0
            imu_timeout_drop = 1
        else: imusentence = "$IIXDR,imu.py_script_fail*39"

    ##### VK-172 GPS USB DONGLE #####
    gpsready = select.select([gpssock], [], [], .1)
    if gpsready [0]:
        t_gps = hack
        data, addr = gpssock.recvfrom(1024)
        if data == "$IIXDR,GPS_FAIL*7B":
            gpsfail = 1
            if gpsdrop == 1:
                gpssentence = gprmc0
                gpsdrop = 0
            else: gpssentence = data
        else:
            t_gps = hack
            gpsdrop = 1
            gps_timeout_drop = 1
            gpssentence = data.split(',')

            # GPRMC
            if gpssentence[8] != '' and gpssentence[7] != '':
                gpsfail = 0
                course = float(gpssentence[8])
                groundspeed = float(gpssentence[7])
                if (imufail == 0) and (groundspeed < .1):
                    course = heading
                rmc = "GPRMC," + gpssentence[1] + ',' + gpssentence[2] + ',' + gpssentence[3] + ',' + gpssentence[4] + ',' + gpssentence[5] + ',' + gpssentence[6] + ',' + str(groundspeed) + ',' + str(course) + ',' + gpssentence[9] + ',,'
                rmccs = format(reduce(operator.xor,map(ord,rmc),0),'X')
                if len(rmccs) == 1:
                        rmccs = "0" + rmccs
                gprmc = "$" + rmc + "*" + rmccs
                
                gpssentence = gprmc
            else:
                gpsfail = 1
                gpssentence = data
            
            
    if (hack - t_gps) > 10.0:
        gpsfail = 1
        if gps_timeout_drop == 1:
            gpssentence = gprmc0
            gps_timeout_drop = 0
        else: gpssentence = "$IIXDR,gps.py_script_fail*2C"

    ##### DST-800 TRIDUCER #####
    dstready = select.select([dstsock], [], [], .1)
    if dstready[0]:
        t_dst = hack
        data, addr = dstsock.recvfrom(1024)
        if data == "$IIXDR,DST_FAIL*7C":
            vhwfail = 1
            if dstdrop == 0:
                dstsentence = sddpt0 + '\r\n' + yxmtw0 + '\r\n' + vwvhw0 + '\r\n' + vwvlw0
                dstdrop = 1
            else: dstsentence = data
        else:
            dstdrop = 0
            dst_timeout_drop = 0
            dstsentence = data.split(',')
            title = dstsentence[0]
    
            # SDDPT
            if title == "$SDDPT":
                if imufail == 1:
                    depth = round(float(dstsentence[1])*math.cos(math.radians(23)),1)
                else:
                    depth = round(float(dstsentence[1])*math.cos(math.radians(23-roll))*math.cos(math.radians(pitch)),1)
                dpt = "SDDPT," + str(depth) + ",0.50"
                dptcs = format(reduce(operator.xor,map(ord,dpt),0),'X')
                if len(dptcs) == 1:
                    dptcs = "0" + dptcs
                sddpt = "$" + dpt + "*" + dptcs
    
            # YXMTW
            if title == "$YXMTW":
                yxmtw = data
    
            # VWVHW
            if title == "$VWVHW":
                vhwfail = 0
                t_vhw = hack              
                waterspeed = float(dstsentence[5])
                if imufail == 0:
                    sensor_angle = math.fabs(23.0-roll)
                else: sensor_angle = 23.0
                five_knot_correction = -.02 * sensor_angle
                ten_knot_correction = -.03 * sensor_angle - 2
                if sensor_angle > 10.0:
                    ten_knot_correction = sensor_angle * (.035 - .0065 * sensor_angle) - 2
                if waterspeed < 5.0:
                    waterspeed = round(waterspeed + (five_knot_correction * waterspeed / 5), 1)
                else: waterspeed = round((waterspeed + (waterspeed * (ten_knot_correction * (waterspeed - 5) - 2 * five_knot_correction * (waterspeed - 10))) / 50),1)
                vhw = "VWVHW,"
                if imufail == 0:
                    vhw = vhw + str(heading)
                else: vhw = vhw + ''
                vhw = vhw + ",T,,M," + str(waterspeed) + ",N,,K"
                vhwcs = format(reduce(operator.xor,map(ord,vhw),0),'X')
                if len(vhwcs) == 1:
                    vhwcs = "0" + vhwcs
                vwvhw = "$" + vhw + "*" + vhwcs
    
            # VWVLW
            if title == "$VWVLW":
                vwvlw = data

            dstsentence = sddpt + '\r\n' + yxmtw + '\r\n' + vwvhw + '\r\n' + vwvlw
            

    if (hack - t_dst) > 10.0:
        if dst_timeout_drop == 1:
            dstsentence = sddpt0 + '\r\n' + yxmtw0 + '\r\n' + vwvhw0 + '\r\n' + vwvlw0
            dst_timeout_drop = 0
        else: dstsentence = "$IIXDR,dst.py_script_fail*2B"

    if (hack - t_vhw) > 10.0:
        vhwfail = 1

    ##### VDR Water Current Set and Drift #####
    if imufail == 0 and gpsfail == 0 and vhwfail == 0:
        vdrfail = 0
        heading_radians = math.radians(heading)
        course_radians = math.radians(course)

        set0 = course_radians - heading_radians
        if set0 < 0:
            set0 = set0 + 2 * math.pi

        drift = math.sqrt(pow(waterspeed,2) + pow(groundspeed,2) - 2 * waterspeed * groundspeed * math.cos(set0))
        if waterspeed == 0 and groundspeed == 0:
            set_relative = set0
        else: set_relative = math.pi - math.atan2(groundspeed * math.sin(set0), waterspeed - groundspeed * math.cos(set0))
        
        set_radians = heading_radians + set_relative
        if set_radians > (2 * math.pi):
            set_radians = set_radians - (2 * math.pi)
        
        # dampen out set and drift over the last ten seconds
        setx_total = setx_total - setx_run[t_ten]
        setx_run[t_ten] = math.cos(set_radians)
        setx_total = setx_total + setx_run[t_ten]
        setx_ave = setx_total / 10
        sety_total = sety_total - sety_run[t_ten]
        sety_run[t_ten] = math.sin(set_radians)
        sety_total = sety_total + sety_run[t_ten]
        sety_ave = sety_total / 10
        set_radians = math.atan2(sety_ave, setx_ave)
        if set_radians < 0:
            set_radians = set_radians + 2 * math.pi

        drift_total = drift_total - drift_run[t_ten]
        drift_run[t_ten] = drift
        drift_total = drift_total + drift_run[t_ten]
        drift = drift_total / 10

        # convert from radians back to degrees
        set_true = math.degrees(set_radians)

        # convert to apparent current
        set_apparent = (set_true - heading) - 180
        if set_apparent < 0:
            set_apparent = set_apparent + 360
            if set_apparent < 0:
                set_apparent = set_apparent + 360

        vdr = "IIVDR,A," + str(int(set_true)) + ",T,,,M," + str(round(drift,1)) + ",N"
        vdrcs = format(reduce(operator.xor,map(ord,vdr),0),'X')
        if len(vdrcs) == 1:
            vdrcs = "0" + vdrcs
        vdrsentence = "$" + vdr + "*" + vdrcs

        mwv = "IIMWV," + str(int(set_apparent)) + ",R," + str(round(drift,1)) + ",N,A"
        mwvcs = format(reduce(operator.xor,map(ord,mwv),0),'X')
        if len(mwvcs) == 1:
            mwvcs = "0" + mwvcs
        mwvsentence = "$" + mwv + "*" + mwvcs

    if imufail == 1 or gpsfail == 1 or vhwfail == 1:
        vdrfail = 1
        setx_total = 0
        setx_run = [0] * 10
        sety_total = 0
        sety_run = [0] * 10
        drift_total = 0
        drift_run = [0] * 10

    if (hack - t_print) > 1.0:
        gonksentence = imusentence + '\r\n' + dstsentence + '\r\n' + gpssentence + '\r\n'
        if vdrfail == 0:
            gonksentence = gonksentence + vdrsentence + '\r\n' + mwvsentence + '\r\n'
        #print gonksentence
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(gonksentence, (GONK_IP, GONK_PORT))
        t_print = hack
        t_ten += 1
        if t_ten > 9:
            t_ten = 0

        if (imusentence == "$IIXDR,imu.py_script_fail*39"):
            t_imu_restart += 1
            if t_imu_restart > 9:
                os.system("pkill -9 -f imu.py")
                os.system("python imu.py &")

        if (gpssentence == "$IIXDR,gps.py_script_fail*2C"):
            t_gps_restart += 1
            if t_gps_restart > 9:
                os.system("pkill -9 -f gps.py")
                os.system("python gps.py &")

        if (dstsentence == "$IIXDR,dst.py_script_fail*2B"):
            t_dst_restart += 1
            if t_dst_restart > 9:
                os.system("pkill -9 -f dst.py")
                os.system("python dst.py &")
            
