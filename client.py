from bluetooth_connector import Bluetoothctl, BluetoothctlError
import bluetooth
import inquirer
import json

connector = Bluetoothctl()

def send_to(target_mac, data):
    print('Connecting to {}'.format(target_mac))
    connector.connect(target_mac)
    port = 1

    socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    socket.connect((target_mac, port))
    print('Successfully connected to {}'.format(target_mac))

    socket.send(json.dumps(data))
    print('Sent data successfully')
    socket.close()

def send_to_display(target_display_name, data):
    nearby_devices = bluetooth.discover_devices(lookup_names=True)
    target_mac = None
    print(nearby_devices)
    for mac, display in nearby_devices:
        print(display)
        if display == target_display_name:
            target_mac = mac
            break
    if target_mac is None:
        raise Exception('NOT FOUND')
    send_to(target_mac, data)


def choose_user_to_connect():
    # Returns the MAC
    nearby_devices = bluetooth.discover_devices(lookup_names=True)
    questions = [
        inquirer.List('device',
            message="Choose immediate device to connect",
            choices=[x for _, x in nearby_devices],
        ),
    ]
    answers = inquirer.prompt(questions)
    for mac, display in nearby_devices:
        if display == answers["device"]:
            return mac


def initiate_client():
    all_devices = ['mustafagoudah-Lenovo-Z51-70', 'Eark', 'Inspiron-7559']
    questions = [
        inquirer.List('device',
            message="Choose target device to send to",
            choices=all_devices,
        ),
    ]
    actual_target = inquirer.prompt(questions)['device']
    print('Discovering in range devices ...')
    immediate_target = choose_user_to_connect()
    payload = {
        'sender': 'SENDER',
        'receiver': actual_target,
        'message': input('Enter message to send')
    }
    send_to(immediate_target, payload)

if __name__ == '__main__':
    initiate_client()
