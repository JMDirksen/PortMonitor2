# Port Monitor

Monitors if TCP ports are accepting connections (if they are open).
It sents errors and reports as push notifications through [Ntfy.sh](https://ntfy.sh/)


## Example

```
sudo apt install python3 python3-pip
python3 -m pip install requests
cd ~
git clone https://github.com/JMDirksen/PortMonitor2.git
cd PortMonitor2
python3 portmonitor.py --ports example.com:80,example.com:81
python3 portmonitor.py --report
```


### Crontab

```
* * * * * python3 ~/PortMonitor2/portmonitor.py --ports example.com:80,example.com:443 --ntfy_topic PortMonitor > /dev/null 2>&1
0 7 * * * python3 ~/PortMonitor2/portmonitor.py --report --ntfy_topic PortMonitor > /dev/null 2>&1
```
