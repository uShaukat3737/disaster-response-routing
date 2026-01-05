# 🚑 Disaster Response Routing System

## 📌 Overview
**Disaster Response Routing** is an advanced algorithmic solution designed to optimize the delivery of life-saving supplies such as **food, medicine, and emergency equipment** in regions affected by natural disasters.  
The system dynamically adapts to damaged infrastructure, changing road conditions, and strict resource constraints to ensure **high-priority zones receive aid in the minimum possible time**.

---

## 🎯 Project Objective
In the aftermath of disasters such as **earthquakes** or **floods**, road connectivity is often severely compromised.  
This project implements a routing system that:

- Models the disaster-affected region as a **weighted undirected graph**  
  \[
  G = (V, E)
  \]
- Accounts for:
  - **Travel cost (time)**
  - **Edge reliability**
- Prioritizes locations based on:
  - Severity of impact
  - Population density
- Computes **optimal delivery routes** for multiple rescue vehicles with **limited carrying capacities**

---

## 🛠️ Core Algorithmic Challenges

- **Graph Uncertainty**  
  Handling roads that may become intermittently unavailable

- **Multi-Objective Optimization**  
  Minimizing travel time while maximizing:
  - Delivery coverage
  - Route reliability

- **Real-Time Replanning**  
  Immediately recomputing alternative paths when a primary route is blocked

- **Scalability**  
  Optimized to handle:
  - Up to **10,000 locations**
  - Over **100,000 road segments**

---

## 🚀 Technical Implementation

### 1️⃣ Mathematical Formulation
The system minimizes the following objective function:

![Objective Function](https://latex.codecogs.com/svg.image?\min\;\alpha\sum_{i\in%20V}(p_i\cdot%20t_i)+\beta\sum_{(u,v)\in%20E}(1-r_{uv})+\gamma\sum_{k\in%20K}\text{idle}_k)

Where:

![Variables](https://latex.codecogs.com/svg.image?\begin{aligned}
p_i&:\text{priority of location }i\\
t_i&:\text{delivery time to location }i\\
r_{uv}&:\text{reliability of road }(u,v)\\
\text{idle}_k&:\text{idle time of vehicle }k\\
\alpha,\beta,\gamma&:\text{weighting parameters}
\end{aligned})

---

### 2️⃣ Algorithms Used

- **Dijkstra & A\***  
  Used for finding the shortest and most reliable paths between the central depot and affected zones

- **Greedy Heuristics**  
  Efficient allocation of:
  - Supplies
  - Vehicle capacity constraints

- **Dynamic Programming**  
  Applied for:
  - Optimal sub-path selection
  - Real-time route adjustments

---

## 📊 Sample Dataset
The project includes a robust simulation environment supporting:

- **50 – 5,000 nodes** representing delivery locations
- **100 – 50,000 edges** representing road networks
- **Randomized resource points**, including:
  - Hospitals
  - Supply depots
  - Emergency hubs

---

## 💻 Requirements

- **Language:** Python  
- **Dependencies:**  
  - Standard Python libraries for:
    - Graph processing
    - Mathematical analysis

---

## 📈 Performance Analysis
The repository includes a detailed **theoretical and empirical scalability report**, covering:

- **Time Complexity**
  - Recursive and non-recursive pathfinding analysis
- **Space Complexity**
  - Memory footprint across varying dataset sizes

---

## 🎓 Academic Context
Developed as a **Design and Analysis of Algorithms (CS2009)** project at  
**FAST-NUCES**.

---
