#!/usr/bin/env python3
"""
DroneVoice Sıfır Bağımlılıklı (Zero-Dependency) WebSocket Köprüsü
Hiçbir harici pip paketi (websockets vb.) gerektirmez!
Sadece Python standart kütüphaneleri (socket, threading, hashlib, base64) kullanır.
Gazebo Sim '/drone/cmd_vel' konusuna doğrudan Twist komutlarını iletir.
"""

import socket
import threading
import hashlib
import base64
import struct
import json
import subprocess
import sys

HOST = "0.0.0.0"
PORT = 9090
MAGIC_STRING = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

def do_handshake(client_socket):
    request = client_socket.recv(2048).decode("utf-8", errors="ignore")
    key = None
    for line in request.split("\r\n"):
        if line.lower().startswith("sec-websocket-key:"):
            key = line.split(":", 1)[1].strip()
            break

    if not key:
        return False

    accept_value = base64.b64encode(
        hashlib.sha1((key + MAGIC_STRING).encode("utf-8")).digest()
    ).decode("utf-8")

    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept_value}\r\n\r\n"
    )
    client_socket.sendall(response.encode("utf-8"))
    return True

def handle_frame(client_socket):
    while True:
        try:
            head = client_socket.recv(2)
            if not head or len(head) < 2:
                break

            b1, b2 = head[0], head[1]
            opcode = b1 & 0x0F

            # 0x8: Bağlantı kapatma frame'i
            if opcode == 0x8:
                break

            masked = (b2 & 0x80) != 0
            payload_len = b2 & 0x7F

            if payload_len == 126:
                payload_len = struct.unpack(">H", client_socket.recv(2))[0]
            elif payload_len == 127:
                payload_len = struct.unpack(">Q", client_socket.recv(8))[0]

            mask = client_socket.recv(4) if masked else b""
            data = bytearray(client_socket.recv(payload_len))

            if masked:
                for i in range(len(data)):
                    data[i] ^= mask[i % 4]

            message_text = data.decode("utf-8", errors="ignore")
            process_rosbridge_message(message_text)

        except (socket.error, ConnectionResetError):
            break
        except Exception as e:
            break

def process_rosbridge_message(raw_msg):
    try:
        data = json.loads(raw_msg)
        op = data.get("op")

        if op == "publish":
            topic = data.get("topic")
            msg = data.get("msg", {})

            if topic == "/drone/cmd_vel":
                linear = msg.get("linear", {})
                angular = msg.get("angular", {})

                lx = float(linear.get("x", 0.0))
                ly = float(linear.get("y", 0.0))
                lz = float(linear.get("z", 0.0))
                wz = float(angular.get("z", 0.0))

                cmd = (
                    f'gz topic -t "/drone/cmd_vel" -m gz.msgs.Twist -p '
                    f'"linear: {{x: {lx:.2f}, y: {ly:.2f}, z: {lz:.2f}}}, angular: {{x: 0, y: 0, z: {wz:.2f}}}"'
                )
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"\r[SESLİ KOMUT ALINDI] Lineer: [{lx:+.1f}, {ly:+.1f}, {lz:+.1f}] | Yaw: {wz:+.1f} m/s", end="", flush=True)

        elif op == "subscribe":
            print(f"\n[*] Abone olunan topic: {data.get('topic')}")

    except Exception:
        pass

def client_worker(client_socket, addr):
    print(f"\n[+] Mobil uygulama bağlandı: {addr[0]}:{addr[1]}")
    try:
        if do_handshake(client_socket):
            handle_frame(client_socket)
    finally:
        client_socket.close()
        print(f"\n[-] Mobil uygulama bağlantısı kapandı: {addr[0]}:{addr[1]}")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print("==================================================")
    print(f"🚀 DroneVoice Sıfır Bağımlılıklı WebSocket Köprüsü!")
    print(f"📡 Dinlenen Port : {PORT}")
    print(f"🛰️ Gazebo Topic  : /drone/cmd_vel (Twist)")
    print("==================================================")
    print("Mobil uygulamadan bağlanmanız bekleniyor...")

    try:
        while True:
            client_socket, addr = server.accept()
            t = threading.Thread(target=client_worker, args=(client_socket, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\nKöprü durduruldu.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
