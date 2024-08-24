import os
import socket
import requests  # py -m pip install requests
import time
import json

# Get/set environment variables / defaults
PORT_LIST = os.getenv('PORT_LIST') or "example.com:80 example.com:443"
INTERVAL = int(os.getenv('INTERVAL') or 300)
NOTIFY_ERROR_COUNT = int(os.getenv('NOTIFY_ERROR_COUNT') or 2)
TIMEOUT = int(os.getenv('TIMEOUT') or 3)
NTFY_TOPIC = os.getenv('NTFY_TOPIC') or "PortMonitor"


def main():
    ports = ports_to_list(PORT_LIST)

    # Load uptimes
    uptime = {}
    if os.path.exists("uptime.json"):
        with open("uptime.json", "r") as file:
            uptime = json.load(file)
    uptimeSamples = 30*24*60*60 / INTERVAL

    while True:
        for port in ports:
            print(f"> {port['string']} ... ", end="", flush=True)

            # Get uptime
            if port['string'] in uptime:
                currentUptime = float(uptime[port['string']])
            else:
                currentUptime = 1.0

            # Check port
            if checkPort(port['address'], port['port']):
                # OK
                newUptime = ( currentUptime * ( uptimeSamples - 1 ) + 1 ) / uptimeSamples
                uptime[port['string']] = newUptime

                # Output / notification
                print(f"OK ({str(round(newUptime*100, 3))}%)", flush=True)
                if port['error_count'] >= NOTIFY_ERROR_COUNT:
                    # Notify back from Error to OK
                    send_notification("OK", f"{port['string']} ({str(round(newUptime*100, 3))}%)")
                port['error_count'] = 0
            else:
                # Error
                port['error_count'] += 1
                newUptime = currentUptime * ( uptimeSamples - 1 ) / uptimeSamples
                uptime[port['string']] = newUptime

                # Output / notification
                print(f"ERROR {port['error_count']} ({str(round(newUptime*100, 3))}%)", flush=True)
                if port['error_count'] == NOTIFY_ERROR_COUNT:
                    # Notify Error
                    send_notification("Error", f"{port['string']} ({str(round(newUptime*100, 3))}%)", True)

        # Save uptimes
        with open("uptime.json", "w") as file:
            json.dump(uptime, file)
        
        time.sleep(INTERVAL)


def send_notification(title: str, message: str, warning: bool = False):
    prio = "3"
    tag = "+1"
    if warning:
        prio = "5"
        tag = "warning"
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message,
            headers={"Title": title, "Priority": prio, "Tags": tag}
        )
        print("Notification sent", flush=True)
    except Exception as e:
        print(e, end=" ")


def ports_to_list(ports: str) -> list:
    portsList = []
    for portString in ports.split():
        address, port = portString.split(':')
        portsList.append(
            {'string': portString, 'address': address,
                'port': int(port), 'error_count': 0}
        )
    return portsList


def checkPort(address: str, port: int):
    try:
        s = socket.socket()
        s.settimeout(TIMEOUT)
        s.connect((address, port))
    except Exception as e:
        return False
    finally:
        s.close()
    return True


if __name__ == "__main__":
    main()
