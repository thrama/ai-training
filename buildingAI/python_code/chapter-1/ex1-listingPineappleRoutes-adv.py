# Define the list of port names and their corresponding numbers
# 0 = PAN (Panama)
# 1 = AMS (Amsterdam)
# 2 = CAS (Casablanca)
# 3 = NYC (New York City)
# 4 = HEL (Helsinki)
portnames = ["PAN", "AMS", "CAS", "NYC", "HEL"]

def permutations(route, ports):
    # If there are remaining ports to visit
    if ports:
        # For each remaining available port
        for i in range(len(ports)):
            # Make recursive call with:
            # - New route: current route + next port
            # - Remaining ports: exclude the port we just added (ports[:i] + ports[i+1:])
            permutations(route + [ports[i]], ports[:i] + ports[i+1:])

    # Base case - no more ports to visit
    else:
        # Only print if we have visited all 5 ports
        if len(route) == 5:
            # Convert port numbers to port names and join with spaces
            print(' '.join([portnames[i] for i in route]))

# Start the recursion:
# - Initial route: [0] (start from Panama)  
# - Available ports: [1,2,3,4] (all other ports)
permutations([0], [1,2,3,4])