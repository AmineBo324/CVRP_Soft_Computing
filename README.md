# CVRP – Soft Computing Contest

## 1. Problem Description

This project addresses the **Capacitated Vehicle Routing Problem (CVRP)** using Soft Computing techniques.
The objective is to minimize the total distance traveled by a fleet of vehicles while respecting vehicle capacity constraints.

Instances are taken from the **Augerat benchmark (Set A and B)**:
[http://vrp.galgos.inf.puc-rio.br/index.php/en/](http://vrp.galgos.inf.puc-rio.br/index.php/en/)

---

## 2. Constraints

A solution is feasible if:

* Each customer is visited exactly once
* Each route starts and ends at the depot (node 1)
* Vehicle capacity is not exceeded
* All customers are served

---

## 3. Input Format

Instances are provided in standard **CVRP Augerat (.vrp)** format.
All teams must use the provided reader function (`reader.py`) to load instances.

---

## 4. Standard Solution Format (MANDATORY)

```python
solution = [
    [1, 5, 9, 12, 1],
    [1, 3, 7, 8, 1]
]
```

Rules:

* Each sublist represents a route
* Depot (node 1) must be the first and last node
* Each customer appears exactly once
* This format is mandatory for Tabu Search, Simulated Annealing, and Genetic Algorithms

---

## 5. Standard Result Format (MANDATORY)

```json
{
  "instance": "A-n32-k5",
  "method": "Tabu Search",
  "best_cost": 845.32,
  "execution_time": 1.27,
  "feasible": true
}
```

---

## 6. Provided Common Functions

The following files must be used by all teams:

* `reader.py` → instance loading
* `cost.py` → cost computation
* `feasibility.py` → solution validation
* `utils.py` → result saving

---

## 7. Team Responsibilities

* **Team 1**: Problem definition, data management, validation, comparison
* **Team 2**: Single-solution metaheuristics (Greedy, Tabu, SA)
* **Team 3**: Genetic Algorithm

---

## 8. Evaluation Criteria

* Execution time
* Best solution cost
* Gap to known optimum
* Average gap and standard deviation

---

## 9. Important Rule

Only **feasible solutions** are considered valid for comparison.
