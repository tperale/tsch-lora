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

LOG_DONE = 0
EB_SENT = 0

def logging_node(log_number):
    global LOG_DONE, EB_SENT
    LOG_DONE = 0
    for i in range(log_number):
        # TODO Wait a random length of time after each log
        reboot_board(node)
        EB_SENT = 0
        start = time.time()
        retry = wait_for_join(node)
        end = time.time()
        print("[node] After %i scan joined in %i after %i EB" % (retry, (end - start), EB_SENT))
        LOG_DONE += 1

def logging_coordinator(log_number):
    global LOG_DONE, EB_SENT
    while LOG_DONE < log_number:
        wait_for(coord, r'\[INFO: TSCH\s*\]\s*TSCH:\senqueue\sEB\spacket')
        print("[coordinator] Sent EB")
        EB_SENT += 1

def start_logging(log_number):
    x = threading.Thread(target=logging_coordinator, args=(log_number,))
    x.start()

    y = threading.Thread(target=logging_node, args=(log_number,))
    y.start()

    x.join()
    y.join()

if __name__ == "__main__":
    start_logging(10)
