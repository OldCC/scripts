import time
import socket
import select
import os
import operator

KPLEX_IP = "127.0.0.1"
KPLEX_PORT = 5005

GONK_IP = "127.0.0.5"
GONK_PORT = 5005
gonksock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
gonksock.bind((GONK_IP, GONK_PORT))

# initialize sentence
gonk_sentence = ''

# timers
t_gonk = time.time()
t_print = time.time()
t_fail = 61

while True:
    
    hack = time.time()

    ##### GONKULATOR #####
    gonkready = select.select([gonksock], [], [], .1)
    if gonkready[0]:
        t_gonk = hack
        t_fail = 60
        data, addr = gonksock.recvfrom(1024)
        gonk_sentence = data

    # If Gonkulator Script Fails...
    if (hack - t_gonk) > 15.0:
        gonk_sentence = "$IIXDR,gonkulator.py_script_fail*54"

    if (hack - t_print) > 1.0:
        t_print = hack
        if gonk_sentence == "$IIXDR,gonkulator.py_script_fail*54":
            t_fail -= 1
            fail_sentence = "IIXDR,restarting," + str(t_fail)
            failcs = format(reduce(operator.xor,map(ord,fail_sentence),0),'X')
            if len(failcs) == 1:
                failcs = "0" + failcs
            fail_sentence = "$" + fail_sentence + "*" + failcs
            gonk_sentence = gonk_sentence + '\r\n' + fail_sentence + '\r\n'
            if t_fail == 0:
                time.sleep(1.5)
                os.system("sudo reboot")
        print gonk_sentence
        kplexsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        kplexsock.sendto(gonk_sentence, (KPLEX_IP, KPLEX_PORT))
        
                
