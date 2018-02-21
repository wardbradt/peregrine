# Bellman Ford Algorithm
This document is a reference for how Bellman-Ford works.

A visual demonstration of Bellman Ford can be found [here](https://algs4.cs.princeton.edu/lectures/44DemoBellmanFord.pdf).

An explanation of the algorithm can be found [here](https://algs4.cs.princeton.edu/44sp/) and [here](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.86.1981&rep=rep1&type=pdf).

This is a simplified version of Bellman-Ford provided by the above link:
```
for (int pass = 0; pass < G.V(); pass++)
   for (int v = 0; v < G.V(); v++)
      for (DirectedEdge e : G.adj(v))
          relax(e);
```

Where `G` is a graph, `G.V()` returns the amount of vertices in `G`, and `G.adj(v))` returns the edges adjacent to `v`.

## Relaxation
Taken from Princeton, "to relax an edge v->w means to test whether the best known way from s to w is to go from s to v, then take the edge from v to w, and, if so, update our data structures."
