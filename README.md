# kts
A Python NMEA-1083 Multiplexer and Data Filtering System

Extracts NMEA-0183 data from the DST-800 Triducer, a BU-353 USB GPS, and an MPU-9250 9-DOF IMU. It corrects sensor measurements for calibration, installation error, "ideal hull" shapes, and calculates the VDR Set and Drift sentence, or the ocean current speed and course.

All these scripts here should be located in the /kts/scripts folder. The RTIMULibCal.ini file should also be located in this folder with these scripts. The RTEllipsoidFit folder should be located in the /kts/ directory.

See kingtidesailing.blogspot.com for more. Keep in mind, this was written by a non-programmer, so it probably is not the most efficient way to do things, and will probably be riddled with errors.
