import bluetooth
import inquirer

from base import BaseSender, ConsoleLogger
from bluetooth_connector import Bluetoothctl
import settings


class ConsoleInputCapturer:
    @staticmethod
    def get_username():
        return input('Please enter your username: ')

    @staticmethod
    def get_input_message():
        return input('Enter a message: ')

    @staticmethod
    def get_immediate_destination():
        nearby_devices = bluetooth.discover_devices(lookup_names=True)
        questions = [
            inquirer.List(
                'device_display',
                message="Choose immediate device to connect",
                choices=[x for _, x in nearby_devices],
            ),
        ]
        device_display = inquirer.prompt(questions)['device_display']
        for mac, display in nearby_devices:
            if display == device_display:
                return mac

    @staticmethod
    def get_final_destination(available_devices):
        questions = [
            inquirer.List(
                'destination_device',
                message="Choose target device to send to",
                choices=available_devices,
            ),
        ]
        return inquirer.prompt(questions)['destination_device']


class Client(BaseSender):

    def __init__(
        self, input_capturer=ConsoleInputCapturer,
        logger=ConsoleLogger, bluetooth_ctl=Bluetoothctl(),
        available_devices=[]
    ):
        super().__init__(logger, bluetooth_ctl)
        self.input_capturer = input_capturer
        self.available_devices = available_devices
        self.logger.debug('Client started')

    def start(self):
        immediate_destination = self.input_capturer.get_immediate_destination()
        final_destination = self.input_capturer.get_final_destination(self.available_devices)
        payload = {
            'source': self.input_capturer.get_username(),
            'destination': final_destination,
            'message': self.input_capturer.get_input_message()
        }
        self.send_to(immediate_destination, payload)


if __name__ == '__main__':
    # Either a list of strings (display names, causing the forwarder to scan and match the name to mac)
    # or, provide a list of tuples (MAC, DISPLAY) such that it skips the discovery and sends right away

    available_devices = settings.AVAILABLE_DEVICES
    # available_devices = ['Inspiron-7559', 'Eark', 'm3eeza', 'mustafagoudah-Lenovo-Z51-70',]
    if isinstance(available_devices[0], tuple):
        # If the input list contains the MAC, map them to nested tuple (required by inquirer) as (display, value)
        available_devices = [(d, (m, d)) for m, d in available_devices]

    client = Client(available_devices=available_devices)
    client.start()
