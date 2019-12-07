import bluetooth
import copy
import json
import os
import threading
import time
import utils
TOPOLOGY = set()
CLIENT_SOCKETS = {}
# MESSAGES = Queue()
MESSAGES = {}
DISPLAY_NAME = os.environ['NETWORKS_USERNAME']
assert (DISPLAY_NAME is not None)

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
                print("start_client: Connecting to \"%s\" port %s" % (display_name, port,))

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
                    target=receiver,
                    args=[socket, display_name]
                ).start()

                threading.Thread(
                    target=sender,
                    args=[socket, display_name]
                ).start()

                print("start_client: Connected to {} on port {}.".format(display_name, port))

# ============================================================================= #

def flood_control_message(msg):
    for edge in TOPOLOGY:
        points = list(edge)

        destination = points[0] if points[0] != DISPLAY_NAME else points[1]

        new_msg = copy.deepcopy(msg)
        new_msg['destination'] = destination
        new_msg['path'] = utils.get_path(new_msg['source'],new_msg['destination'],TOPOLOGY)
        MESSAGES[new_msg['path'][0]].put(new_msg) 


def update_topology(dictionary):
    global TOPOLOGY

    # If the entire message will be passed,
    # access set dictionary to dictionary['value']

    if(dictionary['event'] == 'connection'):
        TOPOLOGY.add(frozenset([dictionary['point1'], dictionary['point2']]))
    elif(dictionary['event'] == 'disconnection'):
        TOPOLOGY.remove(frozenset([dictionary['point1'], dictionary['point2']]))
    else:
        raise "Control event not recognized"


def receiver(client_socket, name):
    while True:
        try:
            data = client_socket.recv(1024)

            if(data == "ping"):
                continue

            # TODO: Handle routing
            msg = json.loads(data)
            if msg['destination'] == DISPLAY_NAME:
                if msg['type'] == 'control':
                    update_topology(msg)
                else:
                    print(msg)
            else:
                msg['path'].pop(0)
                MESSAGES[DISPLAY_NAME] = msg

                
        except Exception as e:
            print(e)
            continue


def disconnection_detector():
    while True:
        for client in CLIENT_SOCKETS:
            try:
                CLIENT_SOCKETS[client].send("ping")
            except Exception as e:
                pass
                # TODO: Handle disconnection
        time.sleep(5)


def sender(client_socket, name):
    try:
        msg = MESSAGES[name].get()
        client_socket.send(json.dumps(msg))
    except Exception as e:
        pass


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
            name = client_socket.recv(1024) #FIXME
        except Exception as e:
            continue

        print(name)

        CLIENT_SOCKETS[name] = client_socket
        MESSAGES[name] = Queue()

        threading.Thread(target=receiver, args=[
                         client_socket, name]).start()
        threading.Thread(target=sender, args=[
                         client_socket, name]).start()


if __name__ == "__main__":
    threading.Thread(target=start_server, args=(1, )).start()
    threading.Thread(target=disconnection_detector).start()

    while True:
        time.sleep(5)
        start_client()
