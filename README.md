# Domoticz-Growatt-Webserver-Plugin

A Domoticz Python Plugin that can read data from the Growatt webserver interface into your Domoticz.

![devices](https://github.com/sincze/Domoticz-Growatt-Webserver-Plugin/blob/master/Growatt-Image.png)

## ONLY TESTED FOR Raspberry Pi

V1.0.0 With Python version 3.5 & Domoticz V4.11214 (beta) / Domoticz V2020.1 (stable)
V1.0.1 With Python version 3.7 & Domoticz V2022.2 (stable)

## Installation

Assuming that domoticz directory is installed in your home directory.

```bash
cd ~/domoticz/plugins
git clone https://github.com/sincze/Domoticz-Growatt-Webserver-Plugin
cd Domoticz-Growatt-Webserver-Plugin

# restart domoticz:
sudo /etc/init.d/domoticz.sh restart
```
## Known issues

None at the moment

## Updating

Like other plugins, in the Domoticz-Growatt-Webserver-Plugin directory:
```bash
git pull
sudo /etc/init.d/domoticz.sh restart
```

## Parameters

| Parameter | Value |
| :--- | :--- |
| **Server address** | This is the location where the Growatt mobile APP retrieves data from. |
| **Portal Username** | Username of the Inverter portal eg. admin |
| **Portal Password** | Password of the Inverter portal |
| **Protocol** |	For Growatt inverters this is usually HTTP |
| **Debug** | default is 0 |

## Acknowledgements

* Special thanks for all the hard work of [Dnpwwo](https://github.com/dnpwwo), for the examples and fixing the framework for COOKIE usage.
* Domoticz team
