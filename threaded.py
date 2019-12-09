import json
import os
import threading
import time
from queue import Queue

import bluetooth
import inquirer

import utils
from logger import SafeWriter

LOGGER = SafeWriter("log.txt", "w")
TOPOLOGY = set()
SOCKETS = {}
MESSAGES = {}
DISPLAY_NAME = os.environ['NETWORKS_USERNAME']

assert DISPLAY_NAME is not None


def start_client():
    global TOPOLOGY
    service_matches = bluetooth.find_service(name="NetworksTest")

    if len(service_matches) == 0:
        LOGGER.write("Couldn't find the NetworksTest service")
    else:
        for service in service_matches:
            port = service["port"]
            host = service["host"]
            client_name = service["description"]

            # Create the client socket
            if not client_name in SOCKETS:
                LOGGER.write('Connecting to "{}"'.format(client_name))

                socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

                try:
                    socket.connect((host, port))
                    socket.send(DISPLAY_NAME)
                except Exception as e:
                    continue

                socket.settimeout(5.0)
                add_connection(client_name, socket)

                for message in utils.serialize_topology(TOPOLOGY, client_name, DISPLAY_NAME):
                    MESSAGES[client_name].put(message)

                # Flood my own clients, think of the case where:
                #  X - Y && W - Z :: Now Y-W, one edge won't know about the rest of the network.
                flood_control_message('connection', client_name)
                LOGGER.write("Connected to {} on port {}.".format(client_name, port))

# ============================================================================= #


def flood_control_message(event, target_user):
    for destination in utils.get_all_devices(TOPOLOGY, DISPLAY_NAME):
        new_msg = utils.control_message(event, target_user, DISPLAY_NAME)
        new_msg['destination'] = destination
        if not add_to_the_queue(new_msg):
            LOGGER.write('Failed to deliver flood message:')
            LOGGER.write('Event: "{}", destination: "{}"'.format(event, destination))


def add_to_the_queue(msg_dict):
    # To be used for data messages
    # Appends the path, and puts it in the queue
    path = utils.get_path(msg_dict['source'], msg_dict['destination'], TOPOLOGY)
    if not path:
        return False
    path.pop(0)  # Remove myself
    msg_dict['path'] = path
    MESSAGES[path[0]].put(msg_dict)
    return True


def update_topology(dictionary):
    global TOPOLOGY

    # If the entire message will be passed,
    # access set dictionary to dictionary['data']

    if(dictionary['event'] == 'connection'):
        TOPOLOGY.add(frozenset([dictionary['point1'], dictionary['point2']]))
    elif(dictionary['event'] == 'disconnection'):
        try:
            TOPOLOGY.remove(frozenset([dictionary['point1'], dictionary['point2']]))
        except KeyError:
            # Edge already removed, probably in disconnection handler
            return
    else:
        raise "Control event not recognized"


def receiver(client_socket, client_name):
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if data == "ping":
                continue

            # TODO: Handle routing
            msg = json.loads(data)
            LOGGER.write('================RECIEVER===============')
            LOGGER.write(json.dumps(msg))
            LOGGER.write('+++++++++++++++++++++++++++++++++++++++')
            if msg['destination'] == DISPLAY_NAME:
                # Message intended for me
                if msg['type'] == 'control':
                    update_topology(msg['data'])
                else:
                    # Data message, should directly print to stdout
                    print(msg['source'], ': ', msg['data'])
            else:
                msg['path'].pop(0)
                next_hop = msg['path'][0]
                MESSAGES[next_hop].put(msg)
        except Exception as e:
            if "timed out" in str(e):
                continue
            else:
                break


def bfs(edge_list, source_node):
    queue = []
    visited = []
    queue.append(source_node)
    visited.append(source_node)
    while not queue:
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


def handle_disconnection(client_name):
    # Remove from topology
    # Flood disconnection

    try:
        TOPOLOGY.remove(frozenset([DISPLAY_NAME, client_name]))
        reachable_nodes = bfs(TOPOLOGY, DISPLAY_NAME)
        for x, y in TOPOLOGY:
            if not x in reachable_nodes:
                TOPOLOGY.remove(frozenset([x, y]))
            if not y in reachable_nodes:
                TOPOLOGY.remove(frozenset([x, y]))
            
    except KeyError:
        # Edge already removed, probably in update topology
        pass

    flood_control_message('disconnection', client_name)

    del SOCKETS[client_name]
    # TODO: Close the thread


def disconnection_detector():
    while True:
        try:
            for name, socket in SOCKETS.items():
                try:
                    socket.send("ping")
                except Exception as e:
                    handle_disconnection(name)
            time.sleep(5)
        except RuntimeError:
            # dictionary changed size during iteration error
            continue


def sender(client_socket, name):
    while True:
        try:
            LOGGER.write('=================SENDER================')
            LOGGER.write('Queue: ')
            LOGGER.write(json.dumps({k: list(v.queue) for k, v in MESSAGES.items()}))
            msg = MESSAGES[name].get(True, None)
            LOGGER.write('Picked message: ')
            LOGGER.write(json.dumps(msg))
            LOGGER.write('+++++++++++++++++++++++++++++++++++++++')
            client_socket.send(json.dumps(msg))
        except Exception as e:
            LOGGER.write(str(e))
            pass
        time.sleep(1)


def start_server(port):
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", port))
    server_sock.listen(port)

    bluetooth.advertise_service(server_sock, "NetworksTest", description=DISPLAY_NAME)

    LOGGER.write("Waiting for connections on RFCOMM channel {}".format(port))

    while True:
        client_socket, client_info = server_sock.accept()
        LOGGER.write('Accepted connection from: "{}"'.format(client_info))

        client_socket.settimeout(5.0)  # Will raise if 'recv' waits for more than 5s

        try:
            # First message will be the display name
            client_name = client_socket.recv(1024)
            client_name = client_name.decode('utf-8')
        except Exception as e:
            continue

        add_connection(client_name, client_socket)

        # Flood connection message
        flood_control_message('connection', client_name)

        for message in utils.serialize_topology(TOPOLOGY, client_name, DISPLAY_NAME):
            MESSAGES[client_name].put(message)


def add_connection(client_name, client_socket):
    TOPOLOGY.add(frozenset([DISPLAY_NAME, client_name]))
    MESSAGES[client_name] = Queue()
    SOCKETS[client_name] = client_socket

    threading.Thread(
        target=receiver,
        args=[client_socket, client_name]

    ).start()

    threading.Thread(
        target=sender,
        args=[client_socket, client_name]
    ).start()


def start_ui_client():
    # Obviously not tested at all.
    while True:
        input('Press Enter to start sending a new message.\n')
        available_devices = utils.get_all_devices(TOPOLOGY, DISPLAY_NAME)
        if len(available_devices) == 0:
            print('Sorry, there are no devices in the network at this time.')
            continue

        questions = [
            inquirer.List(
                'available_devices',
                message="Choose a user to send to",
                choices=available_devices,
            )
        ]
        user_destination = inquirer.prompt(questions)['available_devices']
        message_body = input('Enter message: ')
        message = {
            'source': DISPLAY_NAME,
            'type': 'data',
            'destination': user_destination,
            'data': message_body
        }

        if not add_to_the_queue(message):
            print('Failed to deliver your message to {}.'.format(user_destination))


if __name__ == "__main__":
    import atexit
    # On termination, the log file should be closed.
    atexit.register(lambda: LOGGER.close())

    threading.Thread(target=start_server, args=(1, )).start()
    threading.Thread(target=disconnection_detector).start()
    threading.Thread(target=start_ui_client).start()

    while True:
        time.sleep(5)
        start_client()
