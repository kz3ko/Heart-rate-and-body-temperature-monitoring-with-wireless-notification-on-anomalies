import network
import utime
from umqtt.robust import MQTTClient

class Wireless:

    def __init__(self, name='UPC0666645', password='kN6jQbhfybcs', host = '192.168.0.87', id = '1'):
        """
        Initiation of Wireless class which is responsible for all wireless connections, including WiFi and MQTT.
        Arguments are WiFi name, password, MQTT broker IP and device ID. All are set by default, as its the first
        device made.
        """
        self.name = name
        self.password = password
        self.host_ip = host
        self.device_id = id

        self.wlan = network.WLAN(network.STA_IF)
        self.client = MQTTClient(id, host)

        self.topic = 'esp8266/' + id

    def wifi_connect(self):
        """
        Check connection status with any WiFi network. IF ESP8266 is not connected to any WiFi try to connect
        with declared one. If attempt fails, wait 100ms and try again. Return if device connects succesfully
        or it failes 50 times.
        """
        try:
            attempt = 0
            wlan = self.wlan
            if wlan.isconnected() == False:
                wlan.active(True)
                wlan.connect(self.name, self.password)
                while wlan.isconnected() == False and attempt <= 50:
                    attempt += 1
                    utime.sleep_ms(100)
                    pass
            return
        except:
            return

    def wifi_status(self):
        """ Get status of WiFi connection. """
        return self.wlan.isconnected()

    def mqtt_connect(self):
        """ Connect with declared MQTT client. """
        try:
            self.client.connect()
            self.mqtt_is_connected = True
        except:
            self.mqtt_is_connected = False

    def mqtt_status(self):
        """ Get the MQQT connection status. """
        return self.mqtt_is_connected

    def publish(self, data):
        """ Publish 'data' on set topic. """
        self.client.publish(self.topic, data)