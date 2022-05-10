#Main loop program

#Port 8000 - Compiled code transfer
#Port 8001 - Properties

import marshal
import logging
import inspect
import socket
import sys
import threading
import time
import re
from moduleClass import *
import py_compile

def initialiseSelf():
    file = open ("pi-properties.txt", "r")
    properties = file.readlines()
    if re.search('Wheel',properties[2]):
        thisModule = WheelModule(properties[0][:-1])
    else:
        thisModule = Module(properties[0][:-1])
    devices.append(thisModule)

def networkScan(mode):
    while True:
        for i in range(111,121):
            host = str("192.168.0."+str(i))
            if host != str(devices[0].getIP()):
                sScan = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sScan.settimeout(0.5)
                try:
                    sScan.connect((host, 8001))
                    skip = 0
                    for n in range(0,len(devices)):
                        if (str(host) == str(devices[n].getIP())):
                            skip = 1
                    if skip == 0:
                        inProperties = sScan.recv(1024)
                        splitProperties = inProperties.split()
                        strProperties = [item.decode('ascii') for item in splitProperties]
                        if ('Wheel' in strProperties[2]):
                            devices.append(WheelModule(strProperties[0]))
                            print ("New device added: Wheel - "+strProperties[0])
                        elif ('Sensor' in strProperties[2]):
                            devices.append(SensorModule(strProperties[0]))
                            print ("New device added: Sensor - "+strProperties[0])
                        else:
                            devices.append(Module(strProperties[0]))
                            print ("New device added: Module - "+strProperties[0])
                except Exception as e:
                    pass
                sScan.close()
        if mode == 0: #One time scan
            break

#Listens for devices asking for properties
def propertiesExchange():
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        s.bind((devices[0].getIP(),8001))
        s.listen()
        connection, address = s.accept()
        file = open ("pi-properties.txt", "rb")
        data = file.read(1024)
        connection.sendall(data)
        connection.close()
        s.close()

def inputTask():
    time.sleep(10)
    while True:
        command = str(input("Command: "))
        executed = int(semanticTranslate(command))
        if executed == 0:
            print ("Command executed")
        else:
            print ("Command not executed")
        
def semanticTranslate(command):
    if re.search('move', command, re.IGNORECASE):
        if re.search('forward', command, re.IGNORECASE):
            executed = actuatorMove('forward',10)
            return executed
        elif re.search('backward', command, re.IGNORECASE):
            executed = actuatorMove('backward',10)
            return executed
        else:
            return 1
    else:
        return 1

def actuatorMove(direction,distance):
    for i in range(0,len(devices)):
        if isinstance(devices[i],WheelModule):
            if direction == 'forward':
                py_compile.compile('motorForward.py','motorForward.pyc')
                sendCompiledCode(devices[i].getIP(), open('motorForward.pyc','rb').read(1024))
            elif direction == 'backward':
                py_compile.compile('motorBackward.py','motorBackward.pyc')
                sendCompiledCode(devices[i].getIP(), open('motorBackward.pyc','rb').read(1024))
    return 0

def sendCompiledCode(address, code):
    sOut = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sOut.connect((address,8000))
    sOut.sendall(code)
    sOut.close()

def recieveCompiledCode():
    while True:
        sIn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sIn.bind((devices[0].getIP(),8000))
        sIn.listen() # Accepts up to 6 simultaneous connections
        connection, address = sIn.accept()
        code = connection.recv(1024)
        connection.close()
        file = open ('code.pyc','wb')
        file.write(code)
        file.close()
        file = open('code.pyc','rb')
        file.seek(8)
        exec(marshal.load(file))
        file.close()

devices = []
initialiseSelf()

propertiesExchangeThread = threading.Thread(target=propertiesExchange)
propertiesExchangeThread.start()

networkScanThread = threading.Thread(target=networkScan,args=[1])
networkScanThread.start()
print ("Waiting for initial connections...\n")

recieveCompiledThread = threading.Thread(target=recieveCompiledCode)
recieveCompiledThread.start()

inputThread = threading.Thread(target=inputTask)
inputThread.start()
