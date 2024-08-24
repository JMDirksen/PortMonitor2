# Port Monitor

Monitors if TCP ports are accepting connections (if they are open).
It sents errors and reports as push notifications through [Ntfy.sh](https://ntfy.sh/)


## Example


### Crontab

```
* * * * * python3 ~/PortMonitor2/portmonitor.py --ports example.com:80,example.com:443 --ntfy_topic PortMonitor
0 7 * * * python3 ~/PortMonitor2/portmonitor.py --report --ntfy_topic PortMonitor
```
