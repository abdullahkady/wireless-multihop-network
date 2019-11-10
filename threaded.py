import bluetooth
import threading

client_sockets = {}
my_display_name = "Nav"

def start_client():
    service_matches = bluetooth.find_service( name = "NetworksTest" )

    if len(service_matches) == 0:
        print("Couldn't find the SampleServer service =(")
    else:
        for service in service_matches:
            port = service["port"]
            name = service["name"]
            host = service["host"]
            display_name = service["description"]

            print("Connecting to \"%s\"" % (display_name,))

            # Create the client socket
            sock = BluetoothSocket(bluetooth.RFCOMM )
            sock.connect((host, port))

            print("Connected.")
            sock.send(my_display_name)

            client_sockets[display_name] = sock

def start_server():
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", 1))
    server_sock.listen(1)

    port = 1
    bluetooth.advertise_service(server_sock, "NetworksTest", description=my_display_name)

    print("Waiting for connections on RFCOMM channel %d" % port)

    while True:
        client_sock, client_info = server_sock.accept()
        print("Accepted connection from ", client_info)
        name = client_sock.recv(1024)
        client_sockets[name] = client_socket

if __name__ == "__main__":
    start_client()
    x = threading.Thread(target=start_server)
    x.start()
    x.join()
