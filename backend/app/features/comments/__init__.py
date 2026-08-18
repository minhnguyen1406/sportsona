"""Race comment threads — a Reddit-style comment tree.

Import-free package init (models load without pulling the service, avoiding a
registry↔service circular import — same pattern as the other feature modules).
The interesting bit is the data structure: comments form a **tree** (a forest,
one per race) stored as an *adjacency list* via a self-referential
``parent_id`` FK. See ``service.build_thread`` for the O(n) reconstruction.
"""
