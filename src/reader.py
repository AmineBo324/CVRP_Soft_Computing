def read_cvrp_instance(file_path):
    instance = {
        "name": None,
        "dimension": 0,
        "capacity": 0,
        "coords": {},
        "demands": {},
        "depot": None,
        "optimal": None
    }

    section = None

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith("NAME"):
                instance["name"] = line.split(":")[1].strip()

            elif line.startswith("COMMENT") and "Optimal value" in line:
                try:
                    instance["optimal"] = int(line.split("Optimal value:")[1].split(")")[0])
                except:
                    instance["optimal"] = None

            elif line.startswith("DIMENSION"):
                instance["dimension"] = int(line.split(":")[1])

            elif line.startswith("CAPACITY"):
                instance["capacity"] = int(line.split(":")[1])

            elif line.startswith("NODE_COORD_SECTION"):
                section = "coords"

            elif line.startswith("DEMAND_SECTION"):
                section = "demands"

            elif line.startswith("DEPOT_SECTION"):
                section = "depot"

            elif section == "coords":
                i, x, y = map(int, line.split())
                instance["coords"][i] = (x, y)

            elif section == "demands":
                i, d = map(int, line.split())
                instance["demands"][i] = d

            elif section == "depot":
                if line == "-1":
                    section = None
                else:
                    instance["depot"] = int(line)

    # ---------- FIX ----------
    # Customers are all nodes except the depot
    instance["customers"] = [i for i in instance["demands"].keys() if i != instance["depot"]]

    return instance
