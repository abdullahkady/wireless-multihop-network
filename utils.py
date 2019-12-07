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

    assert source in topology.keys(), 'Such source node doesn\'t exist'
    assert destination in topology.keys(
    ), 'Such destination node doesn\'t exist'

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


def serialize_topology(TOPOLOGY):
    # TOPOLOGY is a set of frozensets (hash-able sets): { {1,2}, {2,3} }
    # Convert them back into 2d lists
    # serializeable_set = [[1,2], [2,3]]
    return [[i for i in edge] for edge in TOPOLOGY]


def control_message(event, point2, display_name):
    msg = {
        'source': display_name,
        'destination': '',
        'data': {},
        'path': []
    }
    msg['type'] = 'control'
    msg['data']['event'] = event
    msg['data']['point1'] = display_name
    msg['data']['point2'] = point2
    return msg


def get_all_devices(topology, self_name):
    devices = set([])

    for x, y in topology:
        devices.add(x)
        devices.add(y)

    try:
        devices.remove(self_name)
    except KeyError:
        pass
