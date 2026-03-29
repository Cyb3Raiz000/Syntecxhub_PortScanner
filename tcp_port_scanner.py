import socket
import threading
from queue import Queue
import logging
import sys
from datetime import datetime

# Logging config (force ensures it always writes)
logging.basicConfig(
    filename="scan_results.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    force=True
)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

NUM_THREADS = 50
results = []
lock = threading.Lock()


def scan_port(host, ip, port, show_closed):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)

        result = sock.connect_ex((ip, port))

        if result == 0:
            status = bcolors.OKBLUE + "[ OPEN ]" + bcolors.ENDC
            should_print = True
        else:
            status = bcolors.FAIL + "[ CLOSED ]" + bcolors.ENDC
            should_print = show_closed

        sock.close()

    except socket.timeout:
        status = "TIMEOUT"
        should_print = show_closed
    except Exception as e:
        status = f"ERROR ({e})"
        should_print = True

    if should_print:
        output = f"[ + ] {host} [{ip}]:{port} ==> {status}"
        print(bcolors.BOLD + bcolors.WARNING + output + bcolors.ENDC)
        logging.info(output)

        with lock:
            results.append(output)


def worker(host, ip, queue, show_closed):
    while True:
        try:
            port = queue.get_nowait()
        except:
            break

        scan_port(host, ip, port, show_closed)
        queue.task_done()


def start_scan(host, ip, start_port, end_port, show_closed):
    print(bcolors.OKGREEN + f"\n[+] Scanning {host} [{ip}] from port {start_port} to {end_port}")
    print(f"[+] Start time: {datetime.now()}\n" + bcolors.ENDC)

    port_queue = Queue()

    for port in range(start_port, end_port + 1):
        port_queue.put(port)

    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, args=(host, ip, port_queue, show_closed))
        t.daemon = True
        t.start()

    port_queue.join()

    print(bcolors.OKGREEN + f"\n[+] Scan complete at: {datetime.now()}" + bcolors.ENDC)


if __name__ == "__main__":

    # Input handling
    if len(sys.argv) == 2:
        target = sys.argv[1]
        start = 1
        end = 1024
    else:
        target = input(bcolors.BOLD+bcolors.HEADER+"\nEnter target host: ")
        start = int(input("\nStart port: "))
        end = int(input("\nEnd port: "))

    # Resolve host ONCE
    try:
        target_ip = socket.gethostbyname(target)
        print(f"\nResolved IP: {target_ip}")
    except socket.gaierror:
        print("Invalid host")
        exit()

    # Mode selection
    print("\nChoose mode:")
    print("\n1. Only OPEN ports")
    print("\n2. OPEN + CLOSED ports")

    choice = input("\nEnter choice "+bcolors.FAIL+"1/2"+bcolors.ENDC+bcolors.HEADER+" ")

    if choice == "1":
        start_scan(target, target_ip, start, end, show_closed=False)
    elif choice == "2":
        start_scan(target, target_ip, start, end, show_closed=True)
    else:
        print("Invalid choice")
