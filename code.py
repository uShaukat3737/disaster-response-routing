"""
Disaster Response Routing System
CS2009 - Design and Analysis of Algorithms
FAST-NU Islamabad | Instructor: Zeshan Khan
Date: 24 November 2025

This program simulates rescue vehicles delivering supplies in a disaster zone
with dynamic road blockages, priority locations, and limited vehicle capacity.
"""

import json
import heapq
import random
import os
from typing import List, Dict, Tuple

# ==================================================================
# 1. DATA STRUCTURES - Represent roads and vehicles
# ==================================================================

class Road:
    """Represents a road between two locations with travel time and reliability"""
    def __init__(self, start: int, end: int, time_cost: int, reliability: float):
        self.start = start
        self.end = end
        self.time_cost = time_cost
        self.reliability = reliability
        self.blocked = False  # True if road is damaged

class RescueVehicle:
    """Represents a rescue vehicle with capacity and current state"""
    def __init__(self, vehicle_id: int, capacity: int):
        self.id = vehicle_id
        self.capacity = capacity
        self.current_capacity = capacity
        
        self.location = 0                    # Current node (starts at depot)
        self.next_location = None            # Next node on current path
        self.movement_progress = 0.0         # 0.0 to 1.0 while moving
        
        self.target_location = None          # Final destination node
        self.path_to_target = []             # Remaining nodes in path
        self.full_route = [0]                # Complete path taken (for reporting)
        
        self.total_time = 0                  # Total travel time
        self.delivered = 0                   # Total demand satisfied
        self.reliability_total = 0.0
        self.edges_used = 0
        
        self.status = "WAITING"              # WAITING or MOVING

# ==================================================================
# 2. PATHFINDING - Find shortest path using Dijkstra (with path reconstruction)
# ==================================================================

def find_shortest_path(node_count: int, roads: List[Road], source: int, destination: int) -> Tuple[float, List[int]]:
    """
    Uses Dijkstra's algorithm to find the fastest path from source to destination
    Returns (total_time, [path]) or (inf, []) if no path exists
    """
    graph = {i: [] for i in range(node_count)}
    
    # Build adjacency list (only non-blocked roads)
    for road in roads:
        if not road.blocked:
            graph[road.start].append((road.end, road.time_cost, road.reliability))
            graph[road.end].append((road.start, road.time_cost, road.reliability))
    
    pq = [(0, source, [])]  # (time, node, path_so_far)
    best_time = {i: float('inf') for i in range(node_count)}
    best_time[source] = 0
    
    while pq:
        time_so_far, current, path = heapq.heappop(pq)
        
        if current == destination:
            return time_so_far, path + [current]
            
        if time_so_far > best_time[current]:
            continue  # Old entry
            
        for neighbor, cost, rel in graph[current]:
            new_time = time_so_far + cost
            if new_time < best_time[neighbor]:
                best_time[neighbor] = new_time
                heapq.heappush(pq, (new_time, neighbor, path + [current]))
    
    return float('inf'), []

# ==================================================================
# 3. MAIN SIMULATION ENGINE
# ==================================================================

def run_disaster_response_simulation(input_data: str) -> List[RescueVehicle]:
    """Main simulation loop - runs until all demand is satisfied"""
    
    data = json.loads(input_data)
    locations = {node['id']: node for node in data['nodes']}
    all_roads = [Road(e['u'], e['v'], e['cost'], e['reliability']) for e in data['edges']]
    vehicles = [RescueVehicle(v['id'], v['capacity']) for v in data['vehicles']]
    
    # Safe zones (depots/hospitals) - vehicles return here to reload
    safe_zones = data.get("hospitals", [0])
    for v in vehicles:
        v.location = safe_zones[0]
        v.full_route = [safe_zones[0]]
    
    # Current remaining demand at each location
    current_demand = {node['id']: node.get('demand', 0) for node in data['nodes']}
    
    # Prevent two vehicles from going to same location
    locked_locations: Dict[int, int] = {}  # location → vehicle_id
    
    total_steps = 1000
    blockage_every = 50
    steps_per_road = 15
    random.seed(42)
    
    print("Starting disaster response simulation...")
    
    for step in range(total_steps):
        
        # Random road damage/repair every N steps
        if step > 0 and step % blockage_every == 0:
            available_roads = [r for r in all_roads if not r.blocked or r.blocked]
            if available_roads:
                road = random.choice(available_roads)
                road.blocked = not road.blocked
                status = "DAMAGED" if road.blocked else "REPAIRED"
                print(f"Step {step}: Road {road.start}-{road.end} {status}")
        
        # Process each vehicle
        for vehicle in vehicles:
            
            # If moving and current road is blocked → stop and replan
            if vehicle.status == "MOVING" and vehicle.next_location is not None:
                blocked = False
                for r in all_roads:
                    if (r.start == vehicle.location and r.end == vehicle.next_location) or \
                       (r.end == vehicle.location and r.start == vehicle.next_location):
                        if r.blocked:
                            blocked = True
                            break
                if blocked:
                    print(f"Vehicle {vehicle.id}: Road blocked! Replanning...")
                    vehicle.status = "WAITING"
                    vehicle.movement_progress = 0.0
                    vehicle.next_location = None
                    vehicle.path_to_target = []
                    if vehicle.target_location in locked_locations:
                        del locked_locations[vehicle.target_location]
                    vehicle.target_location = None
            
            # Vehicle is idle - decide what to do
            if vehicle.status == "WAITING":
                
                # Choose next high-priority location if no current target
                if vehicle.target_location is None:
                    candidates = []
                    for loc_id, demand in current_demand.items():
                        if loc_id not in safe_zones and demand > 0 and loc_id not in locked_locations:
                            priority = locations[loc_id].get('priority', 0)
                            candidates.append((priority, demand, loc_id))
                    
                    # Sort by priority (desc), then demand (desc)
                    candidates.sort(reverse=True)
                    
                    for _, demand_needed, loc_id in candidates:
                        if vehicle.current_capacity >= demand_needed:
                            vehicle.target_location = loc_id
                            locked_locations[loc_id] = vehicle.id
                            print(f"Vehicle {vehicle.id}: Assigned to location {loc_id} (priority {locations[loc_id]['priority']})")
                            break
                    
                    # If nothing to do, return to safe zone
                    if vehicle.target_location is None and vehicle.location not in safe_zones:
                        best_zone = min(safe_zones, 
                                      key=lambda z: find_shortest_path(len(locations), all_roads, vehicle.location, z)[0])
                        vehicle.target_location = best_zone
                
                # Plan path to target
                if vehicle.target_location is not None:
                    time_cost, path = find_shortest_path(len(locations), all_roads, vehicle.location, vehicle.target_location)
                    
                    if time_cost < float('inf') and len(path) > 1:
                        vehicle.path_to_target = path[1:]
                        vehicle.next_location = vehicle.path_to_target.pop(0)
                        vehicle.status = "MOVING"
                        vehicle.movement_progress = 0.0
                    elif len(path) == 1:  # Already at destination
                        if vehicle.target_location not in safe_zones:
                            # Deliver supplies
                            needed = current_demand[vehicle.target_location]
                            delivered = min(vehicle.current_capacity, needed)
                            vehicle.current_capacity -= delivered
                            current_demand[vehicle.target_location] -= delivered
                            vehicle.delivered += delivered
                            
                            if current_demand[vehicle.target_location] == 0:
                                print(f"Location {vehicle.target_location} fully served!")
                            
                            # Release lock
                            if vehicle.target_location in locked_locations:
                                del locked_locations[vehicle.target_location]
                            vehicle.target_location = None
                        else:
                            vehicle.target_location = None  # At safe zone
            
            # Vehicle is moving along a road
            elif vehicle.status == "MOVING":
                vehicle.movement_progress += 1.0 / steps_per_road
                if vehicle.movement_progress >= 1.0:
                    # Arrive at next node
                    for r in all_roads:
                        if (r.start == vehicle.location and r.end == vehicle.next_location) or \
                           (r.end == vehicle.location and r.start == vehicle.next_location):
                            vehicle.total_time += r.time_cost
                            vehicle.reliability_total += r.reliability
                            vehicle.edges_used += 1
                            break
                    
                    vehicle.location = vehicle.next_location
                    vehicle.full_route.append(vehicle.location)
                    vehicle.status = "WAITING"
                    vehicle.movement_progress = 0.0
                    vehicle.next_location = None
        
        # Check if mission complete
        all_served = all(current_demand[i] == 0 for i in current_demand if i not in safe_zones)
        all_home = all(v.location in safe_zones for v in vehicles)
        if all_served and all_home:
            print("All locations served. Mission complete!")
            break
    
    return vehicles

# ==================================================================
# 4. MAIN EXECUTION
# ==================================================================

if __name__ == "__main__":
    filename = "data.json"
    
    if not os.path.exists(filename):
        print(f"ERROR: '{filename}' not found!")
        print("Please create data.json with the sample input from the project.")
        exit()
    
    with open(filename, 'r') as file:
        json_input = file.read()
    
    print("Disaster Response System Starting...")
    print("-" * 60)
    
    result_vehicles = run_disaster_response_simulation(json_input)
    
    print("\n" + "="*60)
    print("MISSION FINAL REPORT")
    print("="*60)
    
    total_time = 0
    total_edges = 0
    total_rel = 0.0
    
    for v in result_vehicles:
        route_str = " → ".join(map(str, v.full_route))
        print(f"Vehicle {v.id} Route: {route_str}")
        print(f"   Delivered: {v.delivered} units")
        print(f"   Travel Time: {v.total_time}")
        print("")
        
        total_time += v.total_time
        total_edges += v.edges_used
        total_rel += v.reliability_total
    
    avg_reliability = total_rel / total_edges if total_edges > 0 else 0
    
    print(f"Total Mission Time: {total_time}")
    print(f"Average Road Reliability: {avg_reliability:.3f}")
    print("="*60)
