### Pineapple route emissions
#
# The program below prints the total emissions on the route PAN, AMS, CAS, NY, HEL (in port 
# indices route 0, 1, 2, 3, 4) in kilograms, which is 504.5 kg. Modify the program so that it prints 
# out the carbon emissions of all the possible routes. The solution for the previous exercise should 
# be useful here.
#
# Output Example
# PAN AMS CAS NYC HEL 427.1 kg
#
# ...
#
# PAN CAS AMS NYC HEL 495.5 kg
# Tip: Your values might be different, but the formatting should be identical.
#
###


def calculate_routes():
    # Initialize an empty list to store the routes
    routes = []

    # Start from port 0 and iterate through all combinations of ports 1 to 4
    port1 = 0
    for port2 in range(1, 5):
        for port3 in range(1, 5):
            for port4 in range(1, 5):
                for port5 in range(1, 5):
                    # Create a route list with the current combination of ports
                    route = [port1, port2, port3, port4, port5]

                    # Check if all ports in the route are unique
                    if len(set(route)) == 5:
                        # If unique, add the route to the routes list
                        routes.append(route)

    # Return the list of unique routes
    return routes

def main():
    # List of port names corresponding to their indices
    portnames = ["PAN", "AMS", "CAS", "NYC", "HEL"]

    # Distance matrix (in km) between the ports
    # Source: https://sea-distances.org/
    D = [
            [0,8943,8019,3652,10545],
            [8943,0,2619,6317,2078],
            [8019,2619,0,5836,4939],
            [3652,6317,5836,0,7825],
            [10545,2078,4939,7825,0]
        ]

    # CO2 emissions per km per metric ton (in kg)
    # Source: https://timeforchange.org/co2-emissions-shipping-goods
    co2 = 0.020

    # Calculate all unique routes
    routes = calculate_routes()

    # Iterate through each route to calculate distance and emissions
    for r in routes:
        # Calculate the total distance for the current route
        distance = D[r[0]][r[1]] + D[r[1]][r[2]] + D[r[2]][r[3]] + D[r[3]][r[4]]
        # Calculate the CO2 emissions for the current route
        emissions = distance * co2
        # Print the route and its corresponding CO2 emissions
        print(' '.join([portnames[i] for i in r]) + " %.1f kg" % emissions)
        
# Execute the main function
main()