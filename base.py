import json
import bluetooth as pybluez
from pexpect.exceptions import TIMEOUT

import settings


class ConsoleLogger:
    @staticmethod
    def debug(msg, msg_type='INFO'):
        print('[{}] - {}'.format(msg_type, msg))

    @staticmethod
    def on_message_received(msg, sender):
        # A message that is intended to the server, not just to
        # be forwarded (actually displayed to the end user)
        print('{}:: {}'.format(sender, msg))

    @staticmethod
    def on_traffic(payload, device, traffic_direction):
        # Logging any traffic passing through the server,
        # regardless if it was just acting as a forwarder.
        print('============={} :: {}=============='.format(traffic_direction, device))
        print(payload)
        print('============={} :: {}=============='.format(traffic_direction, device))


class BaseSender:
    bluetooth_ctl = None

    def __init__(self, logger, bluetooth_ctl):
        self.logger = logger
        self.bluetooth_ctl = bluetooth_ctl

    def send_to(self, target_mac, data):
        self.logger.debug('Instantiating bluetooth connection: {}'.format(target_mac))
        self.bluetooth_ctl.connect(target_mac)
        self.logger.debug('Established bluetooth connection: {}'.format(target_mac), msg_type='SUCCESS')

        self.logger.debug('Opening a socket with {}'.format(target_mac))
        socket = pybluez.BluetoothSocket(pybluez.RFCOMM)
        socket.connect((target_mac, settings.PORT))
        self.logger.debug('Socket connected {}'.format(target_mac), msg_type='SUCCESS')

        socket.send(json.dumps(data))
        self.logger.on_traffic(data, target_mac, 'OUTGOING')
        socket.close()
        try:
            # Since some devices are unable to handle multiple (bluetooth) connections at a time
            socket.close()
            self.logger.debug('Socket closed with: {}'.format(target_mac))
            self.bluetooth_ctl.disconnect(target_mac)
        except TIMEOUT:
            pass
