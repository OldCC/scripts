import sys, getopt

sys.path.append('.')
import RTIMU
import os.path
import time
import math
import operator
import socket

IMU_IP = "127.0.0.2"
IMU_PORT = 5005

SETTINGS_FILE = "RTIMULib"

s = RTIMU.Settings(SETTINGS_FILE)
imu = RTIMU.RTIMU(s)

# timers
t_print = time.time()
t_damp = time.time()
t_fail = time.time()
t_shutdown = 0

if (not imu.IMUInit()):
    hack = time.time()
    imu_sentence = "$IIXDR,IMU_FAILED_TO_INITIALIZE*7C"
    if (hack - t_print) > 1.0:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(imu_sentence, (IMU_IP, IMU_PORT))
        t_print = hack
        t_shutdown += 1
        if t_shutdown > 9:
            sys.exit(1)

imu.setSlerpPower(0.02)
imu.setGyroEnable(True)
imu.setAccelEnable(True)
imu.setCompassEnable(True)

poll_interval = imu.IMUGetPollInterval()

# data variables
roll = 0.0
pitch = 0.0
yaw = 0.0
heading = 0.0
rollrate = 0.0
pitchrate = 0.0
yawrate = 0.0
magnetic_deviation = -13.7


# dampening variables
t_one = 0
t_three = 0
roll_total = 0.0
roll_run = [0] * 10
heading_cos_total = 0.0
heading_sin_total = 0.0
heading_cos_run = [0] * 30
heading_sin_run = [0] * 30

# sentences produces by the imu
iihdt0 = "$IIHDT,,T*0C"
iixdr0 = "$IIXDR,A,,D,ROLL,A,,D,PTCH,A,,D,RLLR,A,,D,PTCR,A,,D,YAWR*51"
iihdt = iihdt0
iixdr = iixdr0
freq = 1

while True:
  hack = time.time()

  # if it's been longer than 5 seconds since last print
  if (hack - t_damp) > 5.0:
      
      if (hack - t_fail) > 1.0:
          t_one = 0
          t_three = 0
          roll_total = 0.0
          roll_run = [0] * 10
          heading_cos_total = 0.0
          heading_sin_total = 0.0
          heading_cos_run = [0] * 30
          heading_sin_run = [0] * 30
          imu_sentence = "$IIXDR,IMU_FAIL*6E"
          sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          sock.sendto(imu_sentence, (IMU_IP, IMU_PORT))
          t_fail = hack
          t_shutdown += 1
          if t_shutdown > 29:
              sys.exit(1)

  if imu.IMURead():
    data = imu.getIMUData()
    fusionPose = data["fusionPose"]
    Gyro = data["gyro"]

    if (hack - t_damp) > .1:
        roll = round(math.degrees(fusionPose[0]), 1)
        pitch = round(math.degrees(fusionPose[1]), 1)
        yaw = round(math.degrees(fusionPose[2]), 1)
        rollrate = round(math.degrees(Gyro[0]), 1)
        pitchrate = round(math.degrees(Gyro[1]), 1)
        yawrate = round(math.degrees(Gyro[2]), 1)
        if yaw < 90.1:
            heading = yaw + 270 - magnetic_deviation
        else:
            heading = yaw - 90 - magnetic_deviation
        if heading > 360.0:
            heading = heading - 360.0
            
        # Dampening functions
        roll_total = roll_total - roll_run[t_one]
        roll_run[t_one] = roll
        roll_total = roll_total + roll_run[t_one]
        roll = roll_total / 10
        heading_cos_total = heading_cos_total - heading_cos_run[t_three]
        heading_sin_total = heading_sin_total - heading_sin_run[t_three]
        heading_cos_run[t_three] = math.cos(math.radians(heading))
        heading_sin_run[t_three] = math.sin(math.radians(heading))
        heading_cos_total = heading_cos_total + heading_cos_run[t_three]
        heading_sin_total = heading_sin_total + heading_sin_run[t_three]
        heading = round(math.degrees(math.atan2(heading_sin_total/30,heading_cos_total/30)),1)
        if heading < 0.1:
            heading = heading + 360.0

        t_damp = hack
        t_one += 1
        if t_one == 10:
            t_one = 0
        t_three += 1
        if t_three == 30:
            t_three = 0
  
        if (hack - t_print) > 1:
            hdt = "IIHDT," + str(round(heading))[:-2] + ",T"
            hdtcs = format(reduce(operator.xor,map(ord,hdt),0),'X')
            if len(hdtcs) == 1:
                hdtcs = "0" + hdtcs
            iihdt = "$" + hdt + "*" + hdtcs
        
            xdr = "IIXDR,A," + str(int(round(roll))) + ",D,ROLL,A,"  + str(int(round(pitch))) + ",D,PTCH,A," + str(int(round(rollrate))) + ",D,RLLR,A," + str(int(round(pitchrate))) + ",D,PTCR,A," + str(int(round(yawrate))) + ",D,YAWR"
            xdrcs = format(reduce(operator.xor,map(ord,xdr),0),'X')
            if len(xdrcs) == 1:
                xdrcs = "0" + xdrcs
            iixdr = "$" + xdr + "*" + xdrcs

            imu_sentence = iihdt + '\r\n' + iixdr

            #print imu_sentence
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(imu_sentence, (IMU_IP, IMU_PORT))

            t_print = hack
        
    time.sleep(poll_interval*1.0/1000.0)
