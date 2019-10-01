from bluetooth_connector import Bluetoothctl, BluetoothctlError
import bluetooth
import inquirer

def choose_user_to_connect():
    nearby_devices = bluetooth.discover_devices(lookup_names=True)
    questions = [
        inquirer.List('device',
            message="Choose device to connect?",
            choices=[x for _, x in nearby_devices],
        ),
    ]
    answers = inquirer.prompt(questions)
    for mac, display in nearby_devices:
        if display == answers["device"]:
            return mac

target_mac = choose_user_to_connect()

print('Connecting ...')
connector = Bluetoothctl()
connector.connect(target_mac)

port = 1

socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
socket.connect((target_mac, port))

while True:
    user_input = raw_input('You: ')

    if user_input == 'q':
        socket.close()
        print('bye')
        break


    socket.send(user_input)
    data = socket.recv(1024)
    print('Server: {}'.format(data))
