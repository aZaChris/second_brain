from src.traversal import Related, bfs_related, build_adjacency

EDGES = [
    {"from_node_id": "a", "to_node_id": "b", "relation": "collegato-a", "weight": 0.9},
    {"from_node_id": "b", "to_node_id": "c", "relation": "deriva-da", "weight": 0.7},
]


def test_depth_one_returns_only_direct_neighbors():
    adjacency = build_adjacency(EDGES)
    related = bfs_related("a", adjacency, depth=1)
    assert related == [Related(node_id="b", relation="collegato-a", weight=0.9)]


def test_depth_two_reaches_second_hop():
    adjacency = build_adjacency(EDGES)
    related = bfs_related("a", adjacency, depth=2)
    node_ids = {r.node_id for r in related}
    assert node_ids == {"b", "c"}


def test_isolated_node_has_no_related():
    adjacency = build_adjacency(EDGES)
    assert bfs_related("isolated", adjacency, depth=1) == []


def test_depth_greater_than_graph_extent_does_not_error():
    adjacency = build_adjacency(EDGES)
    related = bfs_related("a", adjacency, depth=50)
    node_ids = {r.node_id for r in related}
    assert node_ids == {"b", "c"}


def test_relation_is_visible_from_both_directions():
    adjacency = build_adjacency(EDGES)
    related_from_b = bfs_related("b", adjacency, depth=1)
    node_ids = {r.node_id for r in related_from_b}
    assert node_ids == {"a", "c"}
