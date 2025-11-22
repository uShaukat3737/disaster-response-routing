# visualize_matplotlib.py 
import json
import matplotlib.pyplot as plt
import networkx as nx
from code import run_disaster_response_simulation

# Load your data (any size)
with open("data.json") as f:
    data = json.load(f)

# Run simulation
print("Running simulation...")
vehicles = run_disaster_response_simulation(open("data.json").read())

# Build graph
G = nx.Graph()
for node in data["nodes"]:
    G.add_node(node["id"], demand=node["demand"], priority=node.get("priority", 0))

for edge in data["edges"]:
    G.add_edge(edge["u"], edge["v"], 
               cost=edge["cost"], 
               reliability=edge["reliability"])

# Hospital nodes
hospitals = set(data.get("hospitals", [0]))

# === PLOT ===
plt.figure(figsize=(14, 10))
plt.title("Disaster Response Routing System ", fontsize=18, fontweight='bold')

# Node colors
node_colors = []
for node in G.nodes():
    if node in hospitals:
        node_colors.append('#2ca02c')    # Green = Hospital
    elif G.nodes[node]['priority'] >= 4:
        node_colors.append('#d62728')    # Red = High priority
    elif G.nodes[node]['demand'] > 0:
        node_colors.append('#ff7f0e')    # Orange = Demand
    else:
        node_colors.append('#1f77b4')    # Blue = Normal

# Node sizes
node_sizes = [800 if node in hospitals else 500 for node in G.nodes()]

# Draw graph with spring layout (beautiful every time)
pos = nx.spring_layout(G, seed=42, k=0.9, iterations=50)

nx.draw(G, pos,
        node_color=node_colors,
        node_size=node_sizes,
        with_labels=True,
        font_size=10,
        font_color='white',
        font_weight='bold',
        edge_color='gray',
        alpha=0.8)

# === DRAW VEHICLE ROUTES ON TOP (THIS IS THE MONEY SHOT) ===
colors = ['#d62728', '#ff7f0e', '#2ca02c', '#9467bd', '#8c564b']
for idx, v in enumerate(vehicles):
    if len(v.full_route) > 1:
        path = v.full_route
        path_edges = list(zip(path, path[1:]))
        nx.draw_networkx_edges(G, pos,
                               edgelist=path_edges,
                               edge_color=colors[idx % len(colors)],
                               width=4,
                               alpha=0.9,
                               style='solid')
        
        # Start & end markers
        nx.draw_networkx_nodes(G, pos,
                               nodelist=[path[0]],
                               node_color='lime',
                               node_shape='s',
                               node_size=800,
                               label=f"V{v.id} Start")
        
        nx.draw_networkx_nodes(G, pos,
                               nodelist=[path[-1]],
                               node_color='red',
                               node_shape='^',
                               node_size=800)

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#2ca02c', label='Hospital / Depot'),
    Patch(facecolor='#d62728', label='High Priority'),
    Patch(facecolor='#ff7f0e', label='Demand Node'),
    Patch(facecolor='gray', label='Roads'),
]
for i, v in enumerate(vehicles):
    legend_elements.append(Patch(facecolor=colors[i % len(colors)], label=f'Vehicle {v.id} Route'))

plt.legend(handles=legend_elements, loc='upper left', fontsize=12)

plt.tight_layout()
plt.axis('off')
plt.savefig("disaster_response_map.png", dpi=300, bbox_inches='tight')


print("Visualization saved as: disaster_response_map.png")
print("OPEN IT")

plt.show()