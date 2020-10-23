import serial
import time
import threading
import re

COORDINATOR_PORT='/dev/ttyUSB0'
NODE_PORT='/dev/ttyUSB1'

coord = serial.Serial(COORDINATOR_PORT, 115200, timeout=1)
node = serial.Serial(NODE_PORT, 115200, timeout=1)

def wait_for(ser, reg):
    out = ""
    out += ser.readline().decode('utf-8')
    while not re.search(reg, out):
        out += ser.readline().decode('utf-8')
    return out

def wait_for_console(ser):
    out = ser.read(100).decode('utf-8')
    while not re.search(r"(#\w{4}.\w{4}.\w{4}.\w{4}>)", out):
        out += ser.read(100).decode('utf-8')

def reboot_board(ser):
    ser.write(b'reboot\r\n')
    wait_for(ser, r"(\[INFO: Zoul( *)\]).*")
    ser.write(b'\r\n')
    wait_for_console(ser)

def wait_for_join(ser):
    count = 0
    line = ser.readline().decode('utf-8')
    while not re.search(r'\[INFO: TSCH\s*\]\s+association\s+done', line):
        line = ser.readline().decode('utf-8')
        count += 1

    return count

def wait_for_drift(ser):
    reg = r"\[INFO: TSCH-LOG\s*\]\s*{asn (\w|\.)* link\s*\d\s*\d\s*\d\s*\d\s*\d\s*ch\s*(\d)}\s*\w\w-\d-\d\s*(tx|rx)\s*LL-\w{4}->LL-\w{4},\s*len\s*(\d*),\s*seq\s*(\d*),\s*(.*),\s*dr\s*(-?\d*)"
    while True:
        line = ser.readline().decode('utf-8')
        r = re.search(reg, line)
        if r:
            return r

RX_ASN = []
RX_CH = []
RX_DR = []

CURR_LOG = 0

def logging_node(log_number):
    global RX_ASN, RX_CH, RX_DR, CURR_LOG
    reboot_board(node)
    wait_for_join(node)
    while CURR_LOG < log_number:
        # TODO Wait a random length of time after each log
        r = wait_for_drift(node)
        asn = r.group(0)
        ch = r.group(1)
        dr = r.group(6)
        RX_ASN.append(asn)
        RX_CH.append(ch)
        RX_DR.append(dr)
        CURR_LOG += 1

def logging_coordinator(log_number):
    global CURR_LOG
    reboot_board(coord)
    while CURR_LOG < log_number:
        time.sleep(0.1)

def start_logging(log_number):
    x = threading.Thread(target=logging_coordinator, args=(log_number,))
    x.start()

    y = threading.Thread(target=logging_node, args=(log_number,))
    y.start()

    x.join()
    y.join()

if __name__ == "__main__":
    start_logging(100)
    print("----- ASN")
    print(*RX_ASN, sep="\n")
    print("----- CH")
    print(*RX_CH, sep="\n")
    print("----- DR")
    print(*RX_DR, sep="\n")
