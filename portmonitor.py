import argparse
import json
import os
import requests  # py -m pip install requests
import socket

parser = argparse.ArgumentParser()
parser.add_argument("--ports", default="example.com:80,example.com:443")
parser.add_argument("--notify_on_errors", default=2, type=int)
parser.add_argument("--timeout", default=3, type=int)
parser.add_argument("--ntfy_topic", default="PortMonitor")
args = parser.parse_args()


def main():
    uptimeSamples = 30*24*60
    ports = ports_to_list(args.ports)

    # Load db
    if os.path.exists("db.json"):
        with open("db.json", "r") as file:
            db = json.load(file)
    else:
        db = {}

    for port in ports:
        print(f"> {port["name"]} ... ", end="", flush=True)

        # Check db
        if not port["name"] in db:
            db[port["name"]] = {"uptime": 1.0, "errors": 0}

        # Get uptime and errors
        uptime = float(db[port["name"]]["uptime"])
        errors = db[port["name"]]["errors"]

        # Check port
        if checkPort(port["address"], port["port"]):
            # OK
            uptime = ( uptime * ( uptimeSamples - 1 ) + 1 ) / uptimeSamples

            # Output / notification
            print(f"OK ({str(round(uptime*100, 3))}%)", flush=True)
            if errors >= args.notify_on_errors:
                # Notify back from Error to OK
                send_notification("OK", f"{port["name"]} ({str(round(uptime*100, 3))}%)")
            errors = 0
        else:
            # Error
            errors += 1
            uptime = uptime * ( uptimeSamples - 1 ) / uptimeSamples

            # Output / notification
            print(f"ERROR {errors} ({str(round(uptime*100, 3))}%)", flush=True)
            if errors == args.notify_on_errors:
                # Notify Error
                send_notification("Error", f"{port["name"]} ({str(round(uptime*100, 3))}%)", True)
        
        # Update db
        db[port["name"]]["errors"] = errors
        db[port["name"]]["uptime"] = uptime

    # Save db
    with open("db.json", "w") as file:
        json.dump(db, file)


def send_notification(title: str, message: str, warning: bool = False):
    prio = "3"
    tag = "+1"
    if warning:
        prio = "5"
        tag = "warning"
    try:
        requests.post(
            f"https://ntfy.sh/{args.ntfy_topic}",
            data=message,
            headers={"Title": title, "Priority": prio, "Tags": tag}
        )
        print("Notification sent", flush=True)
    except Exception as e:
        print(e, end=" ")


def ports_to_list(ports: str) -> list:
    portsList = []
    for portString in ports.replace(" ", ",").replace(";", ",").split(","):
        if not portString:
            continue
        try:
            address, port = portString.split(":")
        except:
            print(f"Bad format: \"{portString}\"")
            continue
        portsList.append(
            {"name": portString, "address": address,
                "port": int(port), "error_count": 0}
        )
    return portsList


def checkPort(address: str, port: int):
    try:
        s = socket.socket()
        s.settimeout(args.timeout)
        s.connect((address, port))
    except Exception as e:
        return False
    finally:
        s.close()
    return True


if __name__ == "__main__":
    main()
