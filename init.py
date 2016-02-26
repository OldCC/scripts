#!/usr/bin/env python

import time
import os
import sys

# start the data inputs
os.system("python /home/pi/kts/scripts/imu.py &")
os.system("python /home/pi/kts/scripts/gps.py &")
os.system("python /home/pi/kts/scripts/dst.py &")

# wait 5 seconds to make sure they're inputing data
time.sleep(10)
os.system("python /home/pi/kts/scripts/gonkulator.py &")

# wait a little longer to make sure all sentences are correct
time.sleep(10)
os.system("python /home/pi/kts/scripts/go.py &")

# close 'er down
sys.exit(1)

