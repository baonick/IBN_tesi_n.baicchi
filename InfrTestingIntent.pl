% node(Id, Type, HWCaps).
node(gateway, edge, 50).
node(edge1, edge, 200).
node(edge2, edge, 200).
node(edge3, edge, 200).
node(cloud1, cloud, 1000).
node(cloud2, cloud, 1500).

% link(From, To, FeatLat, FeatBw).
% Gateway <-> Edge (Latenza ultra-bassa per l'accesso e banda espansa)
link(gateway, edge1, 2, 500).
link(edge1, gateway, 2, 500).
link(gateway, edge2, 5, 500).
link(edge2, gateway, 5, 500).
link(gateway, edge3, 8, 500).
link(edge3, gateway, 8, 500).

% Edge <-> Edge (Interconnessione locale robusta per service chaining distribuito all'edge)
link(edge1, edge2, 10, 1000).
link(edge2, edge1, 10, 1000).
link(edge2, edge3, 10, 1000).
link(edge3, edge2, 10, 1000).
link(edge1, edge3, 15, 1000).
link(edge3, edge1, 15, 1000).

% Edge <-> Cloud (Latenza ridotta sotto i 50ms per requisiti ibridi, banda elevata)
link(edge1, cloud1, 40, 5000).
link(cloud1, edge1, 40, 5000).
link(edge2, cloud1, 45, 5000).
link(cloud1, edge2, 45, 5000).
link(edge3, cloud2, 40, 5000).
link(cloud2, edge3, 40, 5000).
link(edge1, cloud2, 50, 5000).
link(cloud2, edge1, 50, 5000).
link(edge2, cloud2, 55, 5000).
link(cloud2, edge2, 55, 5000).
link(gateway, cloud1, 45, 2000).
link(cloud1, gateway, 45, 2000).
link(gateway, cloud2, 50, 2000).
link(cloud2, gateway, 50, 2000).

% Cloud <-> Cloud (Dorsale ad altissime prestazioni)
link(cloud1, cloud2, 5, 20000).
link(cloud2, cloud1, 5, 20000).

% Self-links (Necessari per VNF instanziate sullo stesso nodo)
link(N, N, 0, 100000).
