import bluetooth
import json

from client import send_to_display

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

    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    port = 1
    server_sock.bind(("", port))
    server_sock.listen(1)
    print('Server started')

    while True:
        client_sock, address = server_sock.accept()
        print('Accepted connection from {}'.format(address))
        data = json.loads(str(client_sock.recv(1024)))
        handle_message(data)

    client_sock.close()
    server_sock.close()

start_server()
