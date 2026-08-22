"""Pure, dependency-free data structures used by feature modules.

Each lives here (not inside a feature) because it's a general tool with no
knowledge of F1 or the database — which also makes each one trivially unit
testable in isolation:

  - ``Trie``        prefix tree → autocomplete (features/search)
  - ``Graph`` + BFS  adjacency list → shortest path (features/connections)
  - ``DisjointSet`` union-find → duplicate-identity clustering (sports/f1)
"""
