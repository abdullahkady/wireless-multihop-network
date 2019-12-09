def get_path(source, destination, edge_set):
    """
    Get path between source node & destination node using dijkstra
    source: Source Node
    destination: Destination Node
    edge_set: set of frozensets (edges)
    """
    topology = {}
    inf = float('inf')

    for x, y in edge_set:
        topology[x] = topology.get(x, []) + [y]
        topology[y] = topology.get(y, []) + [x]

    if source not in topology:
        return []
    if destination not in topology:
        return []

    distances = {vertex: inf for vertex in topology.keys()}
    previous_vertices = {vertex: None for vertex in topology.keys()}
    distances[source] = 0
    vertices = list(topology.keys()).copy()

    while vertices:
        current_vertex = min(vertices, key=lambda vertex: distances[vertex])
        vertices.remove(current_vertex)
        if distances[current_vertex] == inf:
            break
        for neighbour in topology[current_vertex]:
            alternative_route = distances[current_vertex] + 1
            if alternative_route < distances[neighbour]:
                distances[neighbour] = alternative_route
                previous_vertices[neighbour] = current_vertex

    path, current_vertex = [], destination
    while previous_vertices[current_vertex] is not None:
        path.append(current_vertex)
        current_vertex = previous_vertices[current_vertex]
    if path:
        path.append(current_vertex)

    return path[::-1]


def control_message(event, point1, point2, source=None):
    if source is None:
        source = point2
    msg = {
        'source': source,
        'destination': '',
        'data': {},
        'path': []
    }
    msg['type'] = 'control'
    msg['data']['event'] = event
    msg['data']['point1'] = point1
    msg['data']['point2'] = point2
    return msg


def get_all_devices(topology, self_name):
    devices = set()

    for x, y in topology:
        devices.add(x)
        devices.add(y)

    try:
        devices.remove(self_name)
    except KeyError:
        pass

    return devices


def serialize_topology(topology, destination, source):
    # For the first connection, generate control messages representing the
    # entire topology in terms of control messages.
    return [{**control_message('connection', x, y, source=source), 'destination': destination} for x, y in topology]


def topology_to_list(topology):
    # TOPOLOGY is a set of frozensets (hash-able sets): { {1,2}, {2,3} }
    # Convert them back into 2d lists
    # serializeable_set = [[1,2], [2,3]]
    list_topology = [[i for i in edge] for edge in topology]
    return '\n'.join('{} <=> {}'.format(x, y) for x, y in list_topology)
