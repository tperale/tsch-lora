import time
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

def tx(ser, content):
    ser.write(b'send %s\r\n' % str(content).encode('utf-8'))
    wait_for_console(ser)

def rx(ser):
    ser.write(b'recv\r\n')
    line = ser.readline().decode('utf-8')
    wait_for_console(ser)

    if re.search(r'Recv timed out after 10sec', line):
        return None
    return line

def channel(ser, chan):
    ser.write(b'ch %i\r\n' % chan)
    wait_for(ser, r'Changing to channel')
    wait_for_console(ser)
    time.sleep(0.01)

RX_DONE = 0

def logging_tx(ser, crange):
    global RX_DONE
    reboot_board(ser)
    for i in range(crange):
        for j in range(crange):
            print("[tx] Sending %i" % j)
            while RX_DONE == 1:
                pass
            channel(ser, i)
            time.sleep(0.1)
            tx(ser, j)
            while RX_DONE == 0:
                pass

def logging_rx(ser, crange):
    global RX_DONE
    reboot_board(ser)
    for i in range(crange):
        for j in range(crange):
            print("[rx] Scanning %i" % i)
            time.sleep(1)
            RX_DONE = 0
            channel(ser, i)
            data = rx(ser)
            if data is not None:
                print(data)
            RX_DONE = 1

def test_chan_range(crange):
    x = threading.Thread(target=logging_tx, args=(coord, crange,))
    x.start()

    y = threading.Thread(target=logging_rx, args=(node, crange,))
    y.start()

    x.join()
    y.join()

if __name__ == "__main__":
    test_chan_range(4)
