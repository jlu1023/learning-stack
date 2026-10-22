"""vault_learning.digraph gives the same answers as networkx (when installed)."""
import random

import pytest

from vault_learning import digraph as dg

nx = pytest.importorskip("networkx")


def _pair(seed: int, n: int = 12, p: float = 0.18, dag: bool = False):
    rnd = random.Random(seed)
    names = [f"n{i:02d}" for i in rnd.sample(range(100), n)]
    a, b = dg.DiGraph(), nx.DiGraph()
    a.add_nodes_from(names); b.add_nodes_from(names)
    for i, u in enumerate(names):
        for j, v in enumerate(names):
            if u != v and rnd.random() < p and (not dag or i < j):
                a.add_edge(u, v); b.add_edge(u, v)
    return a, b


@pytest.mark.parametrize("seed", range(40))
def test_components_cycles_and_reachability_match(seed):
    a, b = _pair(seed)
    assert sorted(map(sorted, dg.strongly_connected_components(a))) == \
        sorted(map(sorted, nx.strongly_connected_components(b)))
    canon = lambda cs: sorted(tuple(c[c.index(min(c)):] + c[:c.index(min(c))]) for c in cs)  # noqa: E731
    assert canon(dg.simple_cycles(a)) == canon(nx.simple_cycles(b))
    assert dg.is_directed_acyclic_graph(a) == nx.is_directed_acyclic_graph(b)
    for n in a:
        assert dg.descendants(a, n) == nx.descendants(b, n)


@pytest.mark.parametrize("seed", range(40))
def test_dag_orders_and_reduction_match(seed):
    a, b = _pair(seed, dag=True)
    key = lambda n: (int(n[1:]) % 7, n)  # noqa: E731
    assert list(dg.lexicographical_topological_sort(a, key=key)) == \
        list(nx.lexicographical_topological_sort(b, key=key))
    assert [sorted(g) for g in dg.topological_generations(a)] == \
        [sorted(g) for g in nx.topological_generations(b)]
    assert sorted(dg.transitive_reduction(a).edges()) == sorted(nx.transitive_reduction(b).edges())


def test_subgraph_copy_and_edge_data():
    g = dg.DiGraph()
    g.add_edge("a", "b", n=1); g.add_edge("b", "c"); g.add_edge("c", "a")
    s = g.subgraph(["a", "b"])
    assert list(s.edges()) == [("a", "b")] and s[ "a"]["b"]["n"] == 1
    c = g.copy(); c.remove_edges_from([("c", "a")])
    assert g.has_edge("c", "a") and not c.has_edge("c", "a") and dg.is_directed_acyclic_graph(c)
    assert g.get_edge_data("x", "y", {}) == {} and g.number_of_edges() == 3
    with pytest.raises(ValueError):
        list(dg.lexicographical_topological_sort(g))
