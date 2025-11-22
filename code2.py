import json
import heapq
import random
import os

# --- 1. Simulation Classes ---

class Edge:
    def __init__(self, u, v, cost, reliability):
        self.u = u
        self.v = v
        self.cost = cost
        self.reliability = reliability
        self.is_blocked = False 

class Vehicle:
    def __init__(self, v_id, capacity):
        self.id = v_id
        self.capacity = capacity
        self.remaining_capacity = capacity
        self.current_node = 0
        self.next_node = None
        self.progress = 0.0    
        self.target_node = None
        
        # Stats
        self.route_history = [0]
        self.total_cost = 0
        self.delivered_demand = 0
        self.reliability_sum = 0
        self.edges_count = 0
        
        self.current_path = [] 
        self.state = "IDLE"

# --- 2. Pathfinding (Dijkstra) ---

def dijkstra(num_nodes, edges, start_node, end_node):
    adj = {i: [] for i in range(num_nodes)}
    for e in edges:
        if not e.is_blocked:
            adj[e.u].append((e.v, e.cost, e.reliability))
            adj[e.v].append((e.u, e.cost, e.reliability))

    pq = [(0, start_node, [])]
    visited = set()
    min_costs = {i: float('inf') for i in range(num_nodes)}
    min_costs[start_node] = 0

    while pq:
        cost, u, path = heapq.heappop(pq)
        if u == end_node:
            return cost, path + [u]
        if u in visited:
            continue
        visited.add(u)
        for v, c, r in adj[u]:
            new_cost = cost + c
            if new_cost < min_costs[v]:
                min_costs[v] = new_cost
                heapq.heappush(pq, (new_cost, v, path + [u]))
    
    return float('inf'), []

# --- 3. Simulation Engine ---

def run_simulation(json_data):
    data = json.loads(json_data)
    nodes_dict = {n['id']: n for n in data['nodes']}
    edges_obj_list = [Edge(e['u'], e['v'], e['cost'], e['reliability']) for e in data['edges']]
    vehicles = [Vehicle(v['id'], v['capacity']) for v in data['vehicles']]
    
    # Load Hospitals
    if "hospitals" in data:
        HOSPITALS = data["hospitals"]
    else:
        HOSPITALS = [0]
        print("Warning: 'hospitals' key missing. Defaulting to [0].")

    # Initialize vehicles at first hospital
    for v in vehicles:
        v.current_node = HOSPITALS[0]
        v.route_history = [HOSPITALS[0]]
    
    # Track Live Demand (Mutable)
    live_demands = {n['id']: n['demand'] for n in data['nodes']}
    
    # Track Reserved Nodes (Nodes currently being targeted by a vehicle)
    reserved_targets = {} # {node_id: vehicle_id}

    completed_nodes = set()
    
    total_ticks = 800
    blockage_interval = 50 
    ticks_per_edge = 15.0
    random.seed(42) 

    for tick in range(total_ticks):
        
        # --- A. Blockages ---
        if tick > 0 and tick % blockage_interval == 0:
            valid_edges = [e for e in edges_obj_list]
            if valid_edges:
                target_edge = random.choice(valid_edges)
                target_edge.is_blocked = not target_edge.is_blocked

        # --- B. Vehicle Logic ---
        for v in vehicles:
            
            # 1. Check Blockages
            path_blocked = False
            if v.state == "MOVING":
                for e in edges_obj_list:
                    if ((e.u == v.current_node and e.v == v.next_node) or 
                        (e.v == v.current_node and e.u == v.next_node)):
                        if e.is_blocked:
                            path_blocked = True
                            break
            
            if path_blocked:
                v.state = "IDLE"
                v.progress = 0.0
                v.next_node = None 
                v.current_path = []
                # Release reservation if we were going somewhere but got stuck
                if v.target_node in reserved_targets and reserved_targets[v.target_node] == v.id:
                    del reserved_targets[v.target_node]
                v.target_node = None

            # 2. Decision Making
            if v.state == "IDLE":
                
                # Find NEW Target
                if v.target_node is None:
                    # Identify all nodes that need help
                    potential_targets = []
                    for nid, demand in live_demands.items():
                        if nid not in HOSPITALS and demand > 0:
                            # Check if reserved by SOMEONE ELSE
                            if nid not in reserved_targets:
                                potential_targets.append(nodes_dict[nid])
                    
                    # Sort by Priority (High->Low), then Demand
                    potential_targets.sort(key=lambda x: (-x['priority'], -x['demand']))
                    
                    # Select best fit
                    for cand in potential_targets:
                        if v.remaining_capacity >= live_demands[cand['id']]:
                            v.target_node = cand['id']
                            reserved_targets[cand['id']] = v.id # LOCK THIS TARGET
                            break
                    
                    # If no target, go to Hospital
                    if v.target_node is None:
                        if v.current_node in HOSPITALS:
                            v.target_node = None 
                        else:
                            # Closest Hospital
                            best_h = None
                            min_dist = float('inf')
                            for h in HOSPITALS:
                                dist, _ = dijkstra(len(nodes_dict), edges_obj_list, v.current_node, h)
                                if dist < min_dist:
                                    min_dist = dist
                                    best_h = h
                            if best_h is not None:
                                v.target_node = best_h

                # Plan Path
                if v.target_node is not None:
                    cost, path = dijkstra(len(nodes_dict), edges_obj_list, v.current_node, v.target_node)
                    
                    if cost == float('inf'):
                        pass 
                    elif len(path) > 1:
                        v.current_path = path[1:] 
                        v.next_node = v.current_path.pop(0)
                        v.state = "MOVING"
                        v.progress = 0.0
                    elif len(path) == 1 and v.target_node == v.current_node:
                        # Arrived at Destination
                        if v.target_node not in HOSPITALS:
                            # PICKUP LOGIC
                            demand = live_demands[v.target_node]
                            pickup = min(v.remaining_capacity, demand)
                            
                            v.remaining_capacity -= pickup
                            live_demands[v.target_node] -= pickup # Reduce demand globally
                            v.delivered_demand += pickup
                            
                            if live_demands[v.target_node] == 0:
                                completed_nodes.add(v.target_node)
                            
                            # Release Reservation
                            if v.target_node in reserved_targets and reserved_targets[v.target_node] == v.id:
                                del reserved_targets[v.target_node]
                                
                            v.target_node = None 
                        else:
                            # Arrived at Hospital
                            v.target_node = None 

            elif v.state == "MOVING":
                v.progress += (1.0 / ticks_per_edge)
                if v.progress >= 1.0:
                    # Cost Tracking
                    for e in edges_obj_list:
                        if (e.u == v.current_node and e.v == v.next_node) or (e.v == v.current_node and e.u == v.next_node):
                            v.total_cost += e.cost
                            v.reliability_sum += e.reliability
                            v.edges_count += 1
                            break
                    
                    v.current_node = v.next_node
                    v.route_history.append(v.current_node)
                    v.state = "IDLE"
                    v.progress = 0.0
                    v.next_node = None

        # End condition
        all_cleared = all(d == 0 for nid, d in live_demands.items() if nid not in HOSPITALS)
        all_parked = all(v.current_node in HOSPITALS for v in vehicles)
        if all_cleared and all_parked:
            break

    return vehicles

# --- 4. Main Execution ---

if __name__ == "__main__":
    # File Check
    filename = "data.json"
    if not os.path.exists(filename):
        print(f"Error: '{filename}' not found. Please create it.")
        exit()
        
    with open(filename, 'r') as f:
        json_input = f.read()

    print("Running Simulation with Dynamic Reservations...")
    final_vehicles = run_simulation(json_input)

    # Terminal Report
    print("\n" + "="*30)
    print("FINAL SIMULATION REPORT")
    print("="*30)
    total_combined_cost = 0
    total_edges = 0
    total_reliability = 0

    for v in final_vehicles:
        path_str = " -> ".join(map(str, v.route_history))
        print(f"Vehicle {v.id} Route : {path_str}")
        print(f"Delivered Demand : {v.delivered_demand}")
        print(f"Total Cost : {v.total_cost}")
        print("") 
        total_combined_cost += v.total_cost
        total_edges += v.edges_count
        total_reliability += v.reliability_sum

    avg_reliability = total_reliability / total_edges if total_edges > 0 else 0
    print(f"Total Combined Cost : {total_combined_cost}")
    print(f"Average Reliability : {avg_reliability:.3f}")
    print("="*30 + "\n")
