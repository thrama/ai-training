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