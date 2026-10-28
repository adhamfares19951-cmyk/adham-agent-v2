import socket

ips = [
    ("130.94.58.215", [443, 8443, 80, 8080, 1080, 2083]),
    ("38.54.38.93", [443, 8443, 80, 8080, 1080, 2083]),
]

for ip, ports in ips:
    for port in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        try:
            res = s.connect_ex((ip, port))
            if res == 0:
                print(f"OPEN: {ip}:{port}")
        except Exception as e:
            pass
        finally:
            s.close()
