# import bluetooth

# target_name = "My Phone"
# target_address = None

# nearby_devices = bluetooth.discover_devices()

# for bdaddr in nearby_devices:
#     if target_name == bluetooth.lookup_name( bdaddr ):
#         target_address = bdaddr
#         break

import bluetooth

address = '34:E6:AD:F1:CA:D3'
port = 1

socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
socket.connect((address, port))

while True:
    user_input = input('Message')

    if user_input == 'q':
        socket.close()
        print('bye')
        break


    socket.send(user_input)
    data = socket.recv(1024)
    print('Got from server: {}'.format(data))
