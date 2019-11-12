import json
import os
import threading
import time
import bluetooth

TOPOLOGY = set()
CLIENT_SOCKETS = {}
DISPLAY_NAME = os.environ['NETWORKS_USERNAME']
assert (DISPLAY_NAME is not None)


def serialize_topology():
    # TOPOLOGY is a set of frozensets (hash-able sets): { {1,2}, {2,3} }
    # Convert them back into 2d lists
    # serializeable_set = [[1,2], [2,3]]
    return [[i for i in edge] for edge in TOPOLOGY]


def start_client():
    global TOPOLOGY
    service_matches = bluetooth.find_service(name="NetworksTest")

    if len(service_matches) == 0:
        print("start_client: Couldn't find the NetworksTest service")
    else:
        for service in service_matches:
            port = service["port"]
            host = service["host"]
            display_name = service["description"]

            # Create the client socket
            if not display_name in CLIENT_SOCKETS:
                print("start_client: Connecting to \"%s\" port %s" % (display_name,port,))

                socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

                try:
                    socket.connect((host, port))
                    socket.send(DISPLAY_NAME)
                except Exception as e:
                    continue

                socket.settimeout(5.0)
                CLIENT_SOCKETS[display_name] = socket
                TOPOLOGY.add(frozenset([DISPLAY_NAME, display_name]))

                threading.Thread(
                    target=socket_worker,
                    args=[socket, display_name]).start()

                print(f"start_client: Connected to {display_name} on port {port}.")

# ============================================================================= #


def bfs(edge_list, source_node):
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

    new_topology = TOPOLOGY.copy()
    for edge in TOPOLOGY:
        if source in edge and not edge in incoming_topology:
            new_topology.remove(edge)

    reachable_nodes = bfs(new_topology, DISPLAY_NAME)
    for edge in TOPOLOGY:
        x, y = edge
        if not x in reachable_nodes:
            new_topology.remove(edge)
    TOPOLOGY = new_topology.copy()

    print(f"UPDATED TOPOLOGY FROM {source}")
    print("New Topology: ",TOPOLOGY)

def socket_worker(client_socket, name):
    global TOPOLOGY

    while True:
        print("Socket worker running")

        data = {
            'source': DISPLAY_NAME,
            'data': serialize_topology()
        }

        # Send topology
        print('socket_worker: Sending: ', data)

        try:
            client_socket.send(json.dumps(data))
        except Exception as e:
            print("DISCONNECTION")
            del CLIENT_SOCKETS[name]
            new_topology = TOPOLOGY.copy()
            print('Old Topology: ', TOPOLOGY)
            for edge in TOPOLOGY:
                if edge == frozenset([DISPLAY_NAME, name]):
                    new_topology.remove(edge)
            TOPOLOGY = new_topology.copy()
            print('New Topology: ', TOPOLOGY)
            break

        try:
            data = client_socket.recv(1024)

            update_topology(data)
            print(CLIENT_SOCKETS)
        except Exception as e:
            print(e)
            continue

        time.sleep(5)

def start_server(port):
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", port))
    server_sock.listen(port)

    bluetooth.advertise_service(
        server_sock, "NetworksTest", description=DISPLAY_NAME)

    print("start_server: Waiting for connections on RFCOMM channel %d" % port)

    while True:
        client_socket, client_info = server_sock.accept()
        print("start_server: Accepted connection from ", client_info)

        client_socket.settimeout(5.0)

        try:
            # First message will be the display name
            name = client_socket.recv(1024)
        except Exception as e:
            continue

        print(name)

        CLIENT_SOCKETS[name] = client_socket
        threading.Thread(target=socket_worker, args=[
                         client_socket, name]).start()


if __name__ == "__main__":
    x = threading.Thread(target=start_server, args=(1, ))
    x.start()
    # x.join()

    while True:
        time.sleep(5)
        start_client()
