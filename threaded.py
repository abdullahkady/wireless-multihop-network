import json
import threading
import bluetooth

CLIENT_SOCKETS = {}
DISPLAY_NAME = None
assert (DISPLAY_NAME is not None)

# TODO: Investigate if 2 devices will have 2 channels, we
# need to skip connecting the client if server connected


def serialize_topology():
    # TOPOLOGY is a set of frozensets (hash-able sets): { {1,2}, {2,3} }
    # Convert them back into 2d lists
    # serializeable_set = [[1,2], [2,3]]
    return [[i for i in edge] for edge in TOPOLOGY]


def start_client():
    service_matches = bluetooth.find_service(name="NetworksTest")

    if len(service_matches) == 0:
        print("start_client: Couldn't find the NetworksTest service =(")
    else:
        for service in service_matches:
            port = service["port"]
            host = service["host"]
            display_name = service["description"]

            print("start_client: Connecting to \"%s\"" % (display_name,))

            # Create the client socket
            if display_name in CLIENT_SOCKETS:
                socket = CLIENT_SOCKETS[display_name]
            else:
                socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                socket.connect((host, port))
                CLIENT_SOCKETS[display_name] = socket
                TOPOLOGY.add(frozenset([DISPLAY_NAME, display_name]))
                socket.send(DISPLAY_NAME)

            print("start_client: Connected.")
            data = {
                'source': DISPLAY_NAME,
                'data': serialize_topology()
            }
            print('start_client: Sending: ', data)
            socket.send(json.dumps(data))
            # Wait for the topology reply
            update_topology(socket.recv(1024))

# ============================================================================= #


TOPOLOGY = set()


def update_topology(raw_msg):
    # Parse JSON
    # Build topology
    # {
    #     'source': 'DISPLAY_NAME',
    #     'data': [['EDGES']]
    # }
    raw_msg = json.loads(raw_msg.decode('utf-8'))
    print(raw_msg)
    for edge in raw_msg['data']:
        TOPOLOGY.add(frozenset(edge))


def server_socket_worker(client_socket):
    while True:
        data = client_socket.recv(1024)
        update_topology(data)
        data = {
            'source': DISPLAY_NAME,
            'data': serialize_topology()
        }
        # Reply back with the topology
        print('server_socket_worker: Sending: ', data)
        client_socket.send(json.dumps(data))


def start_server(port):
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", port))
    server_sock.listen(port)

    bluetooth.advertise_service(server_sock, "NetworksTest", description=DISPLAY_NAME)

    print("start_server: Waiting for connections on RFCOMM channel %d" % port)

    while True:
        client_socket, client_info = server_sock.accept()
        print("start_server: Accepted connection from ", client_info)
        name = client_socket.recv(1024)  # First message will be the display name
        CLIENT_SOCKETS[name] = client_socket
        threading.Thread(target=server_socket_worker, args=[client_socket]).start()


if __name__ == "__main__":
    # TODO: Periodically discover?
    x = threading.Thread(target=start_server, args=(1, ))
    x.start()
    # x.join()

    import time
    while True:
        time.sleep(10)
        start_client()
