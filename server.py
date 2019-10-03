import bluetooth
import json
import pexpect

from bluetooth_connector import Bluetoothctl, BluetoothctlError
from client import connector, send_to_display

def start_server():

    def forward_message(data):
        receiver = data['receiver']
        data['receiver'] = '*'
        # Launch a client, connect to 'receiver', send data
        send_to_display(receiver, data)

    def handle_message(data):
        receiver = data.get('receiver')
        sender = data.get('sender')
        message = data.get('message')
        if receiver == '*':
            print('{}: {}'.format(sender, message))
        else:
            forward_message(data)

    print('Server started')

    # forward_message({
    #     'receiver': 'Inspiron-7559',
    #     'sender': 'SENDER',
    #     'message': 'test'
    # })

    while True:
        server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        port = 1
        server_sock.bind(("", port))
        server_sock.listen(1)
        client_sock, address = server_sock.accept()
        print('Accepted connection from {}'.format(address))
        data = client_sock.recv(1024).decode('utf-8')

        data = json.loads(data)
        print(address[0])

        client_sock.close()
        server_sock.close()

        try:
            connector.disconnect(address[0])
        except pexpect.exceptions.TIMEOUT:
            pass

        handle_message(data)

start_server()
