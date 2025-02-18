### Listing Pineapple Routes (Intermediate)
#
# In this exercise you need to list all the possible routes that start from Panama and visit each of 
# the other ports exactly once.
#
# Have a look at the program further down the page. Go ahead and run it. You'll see that the first 
# thing it prints is PAN AMS AMS AMS AMS. Nice for the sailors but bad for pineapple lovers 
# anywhere else but Amsterdam.
#
# Each port is denoted by a number instead of a string: PAN is 0, AMS is 1 and so on. It is often 
# easier to work with integer numbers instead of strings when programming. Keep this mapping in 
# mind when we interpret the results of the program.
#
# Fix the program by adding an if statement that checks that the route includes all of the ports. 
# In other words, check that each of the numbers 0, 1, 2, 3, 4 are included in the list route.
#
# Do not change the print statement given in the template (although you can add more print 
# statements for debugging purposes).
#
# Output Example
# PAN AMS CAS NYC HEL
#
# ...
#
# PAN CAS AMS NYC HEL
# Tip: Your values might be different, but the formatting should be identical.
#
###


def main():
    portnames = ["PAN", "AMS", "CAS", "NYC", "HEL"]

    port1 = 0
    for port2 in range(1, 5):
        for port3 in range(1, 5):
            for port4 in range(1, 5):
                for port5 in range(1, 5):
                    route = [port1, port2, port3, port4, port5]

                    # Modify this if statement to check if the route is valid

                    # set(route) creates a set from the route list, which automatically removes any duplicates
                    # len(set(route)) == 5 checks if the set has 5 elements, meaning there are no duplicates
                    if len(set(route)) == 5:
                        # do not modify this print statement
                        print(' '.join([portnames[i] for i in route]))

main()