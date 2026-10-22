"""A small directed graph and the few algorithms the engine needs, standard
library only (so the plugin needs no installs).

The names and orderings follow networkx, which the engine used before:
iteration is in insertion order, and `lexicographical_topological_sort`
breaks ties by key, then by insertion order, exactly as networkx does.
tests/test_digraph.py checks the results against networkx when it is installed.
"""
from __future__ import annotations

import heapq
from collections import deque


class DiGraph:
    def __init__(self):
        self._succ: dict = {}      # node -> {successor: attributes}
        self._pred: dict = {}      # node -> {predecessor: None}

    # ---------- building ----------
    def add_node(self, n) -> None:
        if n not in self._succ:
            self._succ[n], self._pred[n] = {}, {}

    def add_nodes_from(self, nodes) -> None:
        for n in nodes:
            self.add_node(n)

    def add_edge(self, u, v, **attr) -> None:
        self.add_node(u)
        self.add_node(v)
        self._succ[u].setdefault(v, {}).update(attr)
        self._pred[v][u] = None

    def remove_edges_from(self, edges) -> None:
        for u, v in edges:
            if v in self._succ.get(u, {}):
                del self._succ[u][v]
                del self._pred[v][u]

    def copy(self) -> "DiGraph":
        g = DiGraph()
        g.add_nodes_from(self._succ)
        for u, nbrs in self._succ.items():
            for v, a in nbrs.items():
                g.add_edge(u, v, **a)
        return g

    def subgraph(self, nodes) -> "DiGraph":
        keep = set(nodes)
        g = DiGraph()
        g.add_nodes_from(n for n in self._succ if n in keep)
        for u in g._succ:
            for v, a in self._succ[u].items():
                if v in keep:
                    g.add_edge(u, v, **a)
        return g

    # ---------- reading ----------
    def __iter__(self):
        return iter(self._succ)

    def __contains__(self, n) -> bool:
        return n in self._succ

    def __len__(self) -> int:
        return len(self._succ)

    def __getitem__(self, u) -> dict:
        return self._succ[u]

    @property
    def nodes(self) -> list:
        return list(self._succ)

    def has_edge(self, u, v) -> bool:
        return v in self._succ.get(u, {})

    def successors(self, n):
        return iter(self._succ[n])

    def predecessors(self, n):
        return iter(self._pred[n])

    def edges(self, data: bool = False):
        for u, nbrs in self._succ.items():
            for v, a in nbrs.items():
                yield (u, v, a) if data else (u, v)

    def get_edge_data(self, u, v, default=None):
        return self._succ.get(u, {}).get(v, default)

    def number_of_edges(self) -> int:
        return sum(len(n) for n in self._succ.values())

    def in_degree(self, n) -> int:
        return len(self._pred[n])


# ---------- algorithms ----------
def descendants(g: DiGraph, source) -> set:
    seen, todo = set(), deque([source])
    while todo:
        for w in g.successors(todo.popleft()):
            if w not in seen:
                seen.add(w)
                todo.append(w)
    seen.discard(source)
    return seen


def strongly_connected_components(g: DiGraph):
    """Tarjan's algorithm, iterative (deep prerequisite chains must not hit the
    recursion limit). Yields sets of nodes."""
    index, low, on_stack, stack, counter = {}, {}, set(), [], [0]
    for root in g:
        if root in index:
            continue
        work = [(root, iter(g.successors(root)))]
        index[root] = low[root] = counter[0]; counter[0] += 1
        stack.append(root); on_stack.add(root)
        while work:
            v, it = work[-1]
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter[0]; counter[0] += 1
                    stack.append(w); on_stack.add(w)
                    work.append((w, iter(g.successors(w))))
                    break
                if w in on_stack:
                    low[v] = min(low[v], index[w])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[v])
                if low[v] == index[v]:
                    comp = set()
                    while True:
                        w = stack.pop(); on_stack.discard(w); comp.add(w)
                        if w == v:
                            break
                    yield comp


def simple_cycles(g: DiGraph):
    """Every elementary cycle, each once, starting from its earliest node in
    insertion order. Cycles in note graphs are few and small."""
    order = {n: i for i, n in enumerate(g)}
    for comp in strongly_connected_components(g):
        if len(comp) == 1:
            n = next(iter(comp))
            if g.has_edge(n, n):
                yield [n]
            continue
        for start in sorted(comp, key=order.get):
            allowed = {n for n in comp if order[n] >= order[start]}
            path, on_path = [start], {start}
            stack = [iter(sorted((w for w in g.successors(start) if w in allowed), key=order.get))]
            while stack:
                for w in stack[-1]:
                    if w == start:
                        yield list(path)
                    elif w not in on_path:
                        path.append(w); on_path.add(w)
                        stack.append(iter(sorted((x for x in g.successors(w) if x in allowed),
                                                 key=order.get)))
                        break
                else:
                    stack.pop()
                    on_path.discard(path.pop())


def is_directed_acyclic_graph(g: DiGraph) -> bool:
    indeg = {n: g.in_degree(n) for n in g}
    todo = deque(n for n, d in indeg.items() if d == 0)
    seen = 0
    while todo:
        seen += 1
        for w in g.successors(todo.popleft()):
            indeg[w] -= 1
            if indeg[w] == 0:
                todo.append(w)
    return seen == len(g)


def topological_generations(g: DiGraph):
    indeg = {n: g.in_degree(n) for n in g}
    gen = [n for n, d in indeg.items() if d == 0]
    while gen:
        yield gen
        nxt = []
        for n in gen:
            for w in g.successors(n):
                indeg[w] -= 1
                if indeg[w] == 0:
                    nxt.append(w)
        gen = nxt


def lexicographical_topological_sort(g: DiGraph, key=None):
    """Kahn's algorithm, always taking the smallest available node by key, then
    by insertion order (as networkx does)."""
    key = key or (lambda n: n)
    nid = {n: i for i, n in enumerate(g)}
    indeg = {n: g.in_degree(n) for n in g}
    heap = [(key(n), nid[n], n) for n, d in indeg.items() if d == 0]
    heapq.heapify(heap)
    while heap:
        _, _, n = heapq.heappop(heap)
        yield n
        for w in g.successors(n):
            indeg[w] -= 1
            if indeg[w] == 0:
                heapq.heappush(heap, (key(w), nid[w], w))
    if any(d > 0 for d in indeg.values()):
        raise ValueError("graph contains a cycle")


def transitive_reduction(g: DiGraph) -> DiGraph:
    """The DAG's edges minus every edge implied by a longer path."""
    if not is_directed_acyclic_graph(g):
        raise ValueError("transitive reduction is only defined for a DAG")
    r = DiGraph()
    r.add_nodes_from(g)
    reach = {n: descendants(g, n) for n in g}
    for u in g:
        direct = set(g.successors(u))
        implied = set().union(*(reach[v] for v in direct)) if direct else set()
        for v in g.successors(u):
            if v not in implied:
                r.add_edge(u, v)
    return r
