def get_path(source, destination, edge_list):
    """
    Get path between source node & destination node using dijkstra
    source: Source Node
    destination: Destination Node
    edge_list: frozenset of edges
    """
    topology = {}
    inf = float('inf')

    for x, y in edge_list:
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
