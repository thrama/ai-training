def count11(seq):
    # define this function and return the number of occurrences as a number
    c = 0
    for i in range(len(seq)-1):
        if seq[i] == 1 and seq[i+1] == 1:
            c += 1

    return c

print(count11([0, 0, 1, 1, 1, 0])) # this should print 2