import argparse
import json
import os
import requests  # py -m pip install requests
import socket

parser = argparse.ArgumentParser()
parser.add_argument("--ports", default="example.com:80,example.com:443")
parser.add_argument("--notify_on_errors", default=2, type=int)
parser.add_argument("--timeout", default=3, type=int)
parser.add_argument("--ntfy_topic")
parser.add_argument("--report", nargs="?", const=True, type=bool)
args = parser.parse_args()


def main():

    # Load db
    db_file = os.path.realpath(__file__).replace(".py", ".json")
    if os.path.exists(db_file):
        with open(db_file, "r") as file:
            db = json.load(file)
    else:
        db = {}
    newdb = {}

    # Report only
    if args.report:
        msg = "Uptimes:\n"
        for port in db:
            msg += f"{port} {str(round(db[port]['uptime']*100, 3))}%"
            if db[port]["errors"]:
                msg += f" ({db[port]['errors']} errors)"
            msg += "\n"
        print(msg)
        send_notification("Report", msg, report=True)
        exit()

    uptimeSamples = 30*24*60
    ports = ports_to_list(args.ports)

    for port in ports:
        print(f"> {port['name']} ... ", end="", flush=True)

        # Get uptime and errors
        dbport = db.get(port["name"], {})
        uptime = float(dbport.get("uptime", 1.0))
        errors = int(dbport.get("errors", 0))

        # Check port
        if checkPort(port["address"], port["port"]):
            # OK
            uptime = (uptime * (uptimeSamples - 1) + 1) / uptimeSamples

            # Output / notification
            print(f"OK ({str(round(uptime*100, 3))}%)", flush=True)
            if errors >= args.notify_on_errors:
                # Notify back from Error to OK
                send_notification("OK", f"{port['name']} ({str(round(uptime*100, 3))}%)")
            errors = 0
        else:
            # Error
            errors += 1
            uptime = uptime * (uptimeSamples - 1) / uptimeSamples

            # Output / notification
            print(f"ERROR {errors} ({str(round(uptime*100, 3))}%)", flush=True)
            if errors == args.notify_on_errors:
                # Notify Error
                send_notification("Error", f"{port['name']} ({str(round(uptime*100, 3))}%)", True)

        # Update new db
        newdb[port["name"]] = {"uptime": uptime, "errors": errors}

    # Save new db
    with open(db_file, "w") as file:
        json.dump(newdb, file)


def send_notification(title: str, message: str, warning: bool = False, report: bool = False):
    if not args.ntfy_topic:
        return False
    prio = "3"
    tag = "+1"
    if warning:
        prio = "5"
        tag = "warning"
    if report:
        prio = "2"
        tag = "heavy_check_mark"
    try:
        requests.post(
            f"https://ntfy.sh/{args.ntfy_topic}",
            data=message,
            headers={"Title": title, "Priority": prio, "Tags": tag}
        )
        print(f"Notification sent to {args.ntfy_topic}", flush=True)
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
