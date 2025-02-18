### Listing Pineapple Routes (Advanced)
#
# In this exercise you need to list all the possible routes that start from Panama and visit each of the other ports exactly once.
#
# Have a look at the program further down the page. Go ahead and run it. You'll see that the first thing it prints is PAN AMS AMS 
# AMS AMS. Nice for the sailors but bad for pineapple lovers anywhere else but Amsterdam.
#
# Each port is denoted by a number instead of a string: PAN is 0, AMS is 1 and so on. It is often easier to work with integer 
# numbers instead of strings when programming. Keep this mapping in mind when we interpret the results of the program.
#
# Fix the program by adding an if statement that checks that the route includes all of the ports. In other words, check that each 
# of the numbers 0, 1, 2, 3, 4 are included in the list route.
#
# Do not change the print statement given in the template (although you can add more print statements for debugging purposes).
#
# Output Example
# PAN AMS CAS NYC HEL
#
# ...
#
# PAN CAS AMS NYC HEL
# Tip: Your values might be different, but the formatting should be identical.
#
# Need a hint?
# Note that there is no need to check that no port appears twice. If that were the case, then the route couldn't include all the five 
# ports.
#
###


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