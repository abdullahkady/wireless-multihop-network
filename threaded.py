import json
import os
import threading
import bluetooth

CLIENT_SOCKETS = {}
DISPLAY_NAME = os.environ['NETWORKS_USERNAME']
assert (DISPLAY_NAME is not None)

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

                try:
                    socket.connect((host, port))
                except Exception as e:
                    continue

                CLIENT_SOCKETS[display_name] = socket
                TOPOLOGY.add(frozenset([DISPLAY_NAME, display_name]))

                try:
                    socket.send(DISPLAY_NAME)
                except Exception as e:
                    print("DISCONNECTION")
                    del CLIENT_SOCKETS[display_name]
                    continue

            print("start_client: Connected.")
            data = {
                'source': DISPLAY_NAME,
                'data': serialize_topology()
            }
            print('start_client: Sending: ', data)

            try:
                socket.send(json.dumps(data))

                # Wait for the topology reply
                update_topology(socket.recv(1024))
                print(CLIENT_SOCKETS)
            except Exception as e:
                print("DISCONNECTION")
                del CLIENT_SOCKETS[display_name]

# ============================================================================= #


TOPOLOGY = set()

def bfs(edge_list, source_node):
    # s = set()
    # s.add(frozenset(["Mo","kady"]))
    # s.add(frozenset(["Mo","Nav"]))
    # s.add(frozenset(["Nav","Goudah"]))
    # s.add(frozenset(["Goudah","Amr"]))

    queue = []
    visited = []
    queue.append(source_node)
    visited.append(source_node)
    while not len(queue) == 0:
        u = queue.pop(0)
        for x, y in edge_list:
            if x == u:
                if not y in visited:
                    queue.append(y)
                    visited.append(y)
            if y == u:
                if not x in visited:
                    queue.append(x)
                    visited.append(x)
    return visited

def update_topology(raw_msg):
    # Parse JSON
    # Build topology
    # {
    #     'source': 'DISPLAY_NAME',
    #     'data': [['EDGES']]
    # }
    global TOPOLOGY
    
    raw_msg = json.loads(raw_msg.decode('utf-8'))
    source = raw_msg['source']
    print(raw_msg)
    incoming_topology = set()

    for edge in raw_msg['data']:
        incoming_topology.add(frozenset(edge))
        TOPOLOGY.add(frozenset(edge))

    for edge in TOPOLOGY:
        if source in edge and not edge in incoming_topology:
            TOPOLOGY.remove(edge)

    reachable_nodes = bfs(TOPOLOGY, DISPLAY_NAME)
    new_topology = set()
    for edge in TOPOLOGY:
        x, y = edge
        if x in reachable_nodes:
            new_topology.add(edge)
    TOPOLOGY = new_topology.copy()

def server_socket_worker(client_socket, name):
    while True:
        try:
            data = client_socket.recv(1024)
        except Exception as e:
            print("DISCONNECTION")
            del CLIENT_SOCKETS[name]
            break

        update_topology(data)
        print(CLIENT_SOCKETS)

        data = {
            'source': DISPLAY_NAME,
            'data': serialize_topology()
        }
        # Reply back with the topology
        print('server_socket_worker: Sending: ', data)

        try:
            client_socket.send(json.dumps(data))
        except Exception as e:
            print("DISCONNECTION")
            del CLIENT_SOCKETS[name]
            break


def start_server(port):
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", port))
    server_sock.listen(port)

    bluetooth.advertise_service(server_sock, "NetworksTest", description=DISPLAY_NAME)

    print("start_server: Waiting for connections on RFCOMM channel %d" % port)

    while True:
        client_socket, client_info = server_sock.accept()
        print("start_server: Accepted connection from ", client_info)

        try:
            name = client_socket.recv(1024)  # First message will be the display name
        except Exception as e:
            continue

        CLIENT_SOCKETS[name] = client_socket
        threading.Thread(target=server_socket_worker, args=[client_socket, name]).start()


if __name__ == "__main__":
    x = threading.Thread(target=start_server, args=(1, ))
    x.start()
    # x.join()

    import time
    while True:
        time.sleep(10)
        start_client()
