% =============================================================================
% INFRASTRUTTURA DI TEST PER IL DATASET DI INTENT (context1 .. context34)
% =============================================================================
%
% Topologia FISICA (gerarchica, 3 livelli + accesso):
%
%                 cloud3 ====(1ms,100G)==== cloud4          <- DC centrali (core)
%                   |  (5ms,40G)         (5ms,40G) |
%                 cloud1 ====(1ms,40G)===== cloud2          <- DC metro/regionali
%                 /    \                   /     \
%          (2ms,10G)  (2ms,10G)     (2ms,10G)   (2ms,1G)
%               /        \             /           \
%           edge1 ------------ edge2 ------------- edge3     <- siti edge (anello, 1ms,10G)
%
% =============================================================================

% node(Id, Type, HWCaps).
node(gateway, edge, 32).    % CPE / nodo di accesso, risorse minime
node(edge1, edge, 128).     % sito edge principale
node(edge2, edge, 128).     % sito edge principale
node(edge3, edge, 64).      % sito edge secondario (uplink 1G)
node(cloud1, cloud, 512).   % DC metro A
node(cloud2, cloud, 512).   % DC metro B
node(cloud3, cloud, 2048).  % DC centrale
node(cloud4, cloud, 2048).  % DC centrale

% link(From, To, FeatLat, FeatBw).   [ms, Mbps]

% --- Gateway <-> Edge (accesso diretto) ---
link(gateway, edge1, 1, 1000).
link(edge1, gateway, 1, 1000).
link(gateway, edge2, 1, 1000).
link(edge2, gateway, 1, 1000).
link(gateway, edge3, 1, 1000).
link(edge3, gateway, 1, 1000).

% --- Edge <-> Edge (anello metropolitano) ---
link(edge1, edge2, 1, 10000).
link(edge2, edge1, 1, 10000).
link(edge2, edge3, 1, 10000).
link(edge3, edge2, 1, 10000).
link(edge1, edge3, 1, 10000).
link(edge3, edge1, 1, 10000).

% --- Edge <-> Cloud metro ---
link(edge1, cloud1, 2, 10000).      % diretto
link(cloud1, edge1, 2, 10000).
link(edge2, cloud1, 2, 10000).      % diretto
link(cloud1, edge2, 2, 10000).
link(edge2, cloud2, 2, 10000).      % diretto
link(cloud2, edge2, 2, 10000).
link(edge3, cloud2, 2, 1000).       % diretto, uplink 1G (sito secondario)
link(cloud2, edge3, 2, 1000).
link(edge1, cloud2, 3, 10000).      % edge1-cloud1-cloud2
link(cloud2, edge1, 3, 10000).
link(edge3, cloud1, 3, 10000).      % edge3-edge2-cloud1
link(cloud1, edge3, 3, 10000).

% --- Cloud <-> Cloud (dorsale) ---
link(cloud1, cloud2, 1, 40000).
link(cloud2, cloud1, 1, 40000).
link(cloud1, cloud3, 5, 40000).
link(cloud3, cloud1, 5, 40000).
link(cloud2, cloud4, 5, 40000).
link(cloud4, cloud2, 5, 40000).
link(cloud3, cloud4, 1, 100000).
link(cloud4, cloud3, 1, 100000).
link(cloud1, cloud4, 6, 40000).     % cloud1-cloud2-cloud4
link(cloud4, cloud1, 6, 40000).
link(cloud2, cloud3, 6, 40000).     % cloud2-cloud1-cloud3
link(cloud3, cloud2, 6, 40000).

% Self-links (Necessari per VNF instanziate sullo stesso nodo)
link(N, N, 0, 100000).
