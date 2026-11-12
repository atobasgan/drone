#!/usr/bin/env python3
"""
DroneVoice Lightweight Mobile WebSocket Bridge
Mobil Flutter uygulamasından gelen rosbridge v2.0 JSON Twist mesajlarını
doğrudan Gazebo Sim 'gz topic' veya ROS 2 /drone/cmd_vel konusuna iletir.
"""

import asyncio
import json
import subprocess
import websockets
import sys

PORT = 9090

async def handle_client(websocket):
    print(f"[+] Mobil uygulama bağlandı: {websocket.remote_address}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                op = data.get("op")

                if op == "publish":
                    topic = data.get("topic")
                    msg = data.get("msg", {})

                    if topic == "/drone/cmd_vel":
                        linear = msg.get("linear", {})
                        angular = msg.get("angular", {})

                        lx = linear.get("x", 0.0)
                        ly = linear.get("y", 0.0)
                        lz = linear.get("z", 0.0)
                        wz = angular.get("z", 0.0)

                        # Gazebo Sim topic'ine doğrudan Twist gönder (sim-drone uyumlu)
                        cmd = (
                            f'gz topic -t "/drone/cmd_vel" -m gz.msgs.Twist -p '
                            f'"linear: {{x: {lx:.2f}, y: {ly:.2f}, z: {lz:.2f}}}, angular: {{x: 0, y: 0, z: {wz:.2f}}}"'
                        )
                        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"\r[KOMUT] Lineer: [{lx:+.1f}, {ly:+.1f}, {lz:+.1f}] | Yaw: {wz:+.1f}", end="", flush=True)

                elif op == "subscribe":
                    print(f"[*] Abonelik isteği: {data.get('topic')}")

            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        print(f"\n[-] Mobil uygulama bağlantısı kapandı: {websocket.remote_address}")
    except Exception as e:
        print(f"\n[!] Hata: {e}")

async def main():
    print("==================================================")
    print(f"🚀 DroneVoice Hafif WebSocket Köprüsü Başlatıldı!")
    print(f"📡 Port: {PORT}")
    print("Gazebo Sim '/drone/cmd_vel' konusuna doğrudan yönlendiriliyor...")
    print("==================================================")
    async with websockets.serve(handle_client, "0.0.0.0", PORT):
        await asyncio.Future() # sonsuz döngü

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nKöprü durduruldu.")
        sys.exit(0)

