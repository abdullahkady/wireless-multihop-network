import bluetooth

server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

port = 1
server_sock.bind(("",port))
server_sock.listen(1)
print('Server started')
client_sock, address = server_sock.accept()
print('Accepted connection from {}'.format(address))
while True:
    data = client_sock.recv(1024)
    print('Got: {}'.format(data))
    client_sock.send('ECHO: {}'.format(data))

client_sock.close()
server_sock.close()