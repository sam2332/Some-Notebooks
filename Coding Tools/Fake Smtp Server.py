#!/usr/bin/env python3

import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 25        # Port to listen on (non-privileged ports are > 1023)


def sendData(conn, data):
    data = f'{data}\r\n'.encode('ascii')
    print(">>", data.strip())
    conn.sendall(data)

def getData(conn):
    buff = b''
    while not buff.endswith(b'\r\n'):
        data = conn.recv(1)
        if not data:
            break
        buff += data
    buff = buff.strip()
    return buff


email_num = 0
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    while True:
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            waitingForEnd = False
            sendData(conn,'220 www.localhost.com ESMTP Exim')
            while True:
                buff = getData(conn)
                print("<<", buff)

                if waitingForEnd:
                    if buff == b".":
                        waitingForEnd = False
                        sendData(conn,f'250 Ok: queued as {email_num}')
                        email_num += 1
                    continue

                if buff.startswith(b'EHLO'):
                    sendData(conn,'250 Hello '+buff.replace(b"EHLO",b"").decode('ascii').strip())
                    continue

                if buff.startswith(b'MAIL'):
                    sendData(conn,'250')
                    continue

                if buff.startswith(b'RCPT'):
                    sendData(conn,'250')
                    continue

                if buff.startswith(b'DATA'):
                    sendData(conn,'354 Enter message, ending with "." on a line by itself')
                    waitingForEnd = True
                    continue

                if buff.startswith(b'QUIT'):
                    sendData(conn,'221 Bye')
                    conn.close()
                    break
        print()
        print()
