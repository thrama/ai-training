# this data here is the bag of words representation of This Little Piggy
data = [[1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1],
        [1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 0, 1, 3, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1]]

def distance(row1, row2):
    # fix this function so that it returns 
    # the sum of differences between the occurrences
    # of each word in row1 and row2.
    # you can assume that row1 and row2 are lists with equal length, containing numeric values.
    sum = 0
    for x, y in zip(row1, row2):
        total_distance += abs(x - y)
    return total_distance

def all_pairs(data):
    # this calls the distance function for all the two-row combinations in the data
    # you do not need to change this
    dist = [[distance(sent1, sent2) for sent1 in data] for sent2 in data]
    print(dist)

all_pairs(data)
