svars = {
    "machines": []
}


def add_machine(m):
    added = False
    for i, machine in enumerate(svars["machines"]):
        if machine["name"] == m["name"]:
            svars["machines"][i] = m
            added = True
    if not added:
        svars["machines"] += [
            m
        ]
