import json

import bluetooth as pybluez
from pexpect.exceptions import TIMEOUT

import settings
from base import BaseSender, ConsoleLogger
from bluetooth_connector import Bluetoothctl


class Server(BaseSender):
    server_socket = None

    def __init__(self, logger=ConsoleLogger, bluetooth_ctl=Bluetoothctl()):
        super().__init__(logger, bluetooth_ctl)
        self.logger.debug('Server initiated')

    def _init_socket(self):
        self.server_socket = pybluez.BluetoothSocket(pybluez.RFCOMM)
        self.server_socket.bind(('', settings.PORT))
        self.server_socket.listen(1)
        self.logger.debug('Server listening on port: {}'.format(settings.PORT))

    def _parse_destination_mac_address(self, destination_supplied):
        if isinstance(destination_supplied, (list, tuple)):
            # Allow the destination to be a tuple (converted to a list when serialized) to pass the MAC in case
            # of debugging, where we know that the devices are in-range to avoid an extra devices discovery
            return destination_supplied[0]

        # If the destination provided is a string (assumed to be the display name), discover
        # nearby devices, and return the matching mac address
        self.logger.debug('Discovering target device: {}', format(destination_supplied))
        nearby_devices = pybluez.discover_devices(lookup_names=True)
        return next((mac for mac, display in nearby_devices if display == destination_supplied), None)

    def forward_message(self, data):
        # TODO: Use immediate/actual destination ?
        destination = data['destination']
        destination_mac = self._parse_destination_mac_address(destination)
        if destination_mac is None:
            raise Exception('Device not found!')

        # Override the destination with a '*', to inform the receiver to consume the message, rather than forward it
        data['destination'] = '*'
        self.send_to(destination_mac, data)

    def handle_incoming_data(self, data):
        destination = data.get('destination')
        source = data.get('source')
        message = data.get('message')
        if destination == '*':
            self.logger.debug('Got a message intended for me!')
            self.logger.on_message_received(message, source)
        else:
            self.forward_message(data)

    def listen(self):
        self._init_socket()

        while True:
            client_socket, (mac_address, _) = self.server_socket.accept()
            self.logger.debug('Accepted connection from: {}'.format(mac_address))
            data = json.loads(client_socket.recv(1024).decode('utf-8'))
            self.logger.on_traffic(data, mac_address, 'INCOMING')

            try:
                # Since some devices are unable to handle multiple (bluetooth) connections at a time
                client_socket.close()
                self.logger.debug('Socket closed with: {}'.format(mac_address))
                self.logger.debug('Disconnecting bluetooth connection: {}'.format(mac_address))
                self.bluetooth_ctl.disconnect(mac_address)
            except TIMEOUT:
                self.logger.debug(
                    'Got an exception during bluetooth disconnection: {}'.format(mac_address), msg_type='ERROR'
                )

            self.handle_incoming_data(data)


if __name__ == '__main__':
    server = Server()
    server.listen()
