import serial
import re

COORDINATOR_PORT='/dev/ttyUSB0'

ser = serial.Serial(COORDINATOR_PORT, 115200, timeout=1)

rx = []

def wait_for(reg):
    while not re.search(reg, ser.readline().decode('utf-8')):
        pass

def wait_for_console():
    while not re.search(r"(#\w{4}.\w{4}.\w{4}.\w{4}>)", ser.read(100).decode('utf-8')):

def reboot_board():
    ser.write(b'reboot\r\n')
    wait_for(r"(\[INFO: Zoul( *)\]).*")
    ser.write(b'\r\n')
    wait_for_console()

def log_the_log():
    # TODO Here we must keep the ASN and depending if the timeslot is a TX or RX slot log differently.
    # TODO Coordinators can send back the drift diff and correct the drift while listening nodes are in TX slot
    # TODO Listening node can deduce their drift from the coordinator at each RX slot with packet coming from the coordinator
    line = ser.readline().decode('utf-8')
    while not re.search(r'', line):
        line = ser.readline().decode('utf-8')

    # Get the data from the line
    # r"\[INFO: TSCH-LOG\s*\]\s*\{asn-(\w|\.)* (link-\d-\d-\d-\d)\ ch-(\d+)} (bc-\d-\d) (rx|tx) LL-(\w{4})->LL-(\w{4}), len (\d+), seq (\d+), dr (\d+|-\d+), edr (\d+|-\d+)"

if __name__ == "__main__":
    reboot_board()
