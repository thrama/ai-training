def flip(n):
    odds = 1.0
    pHeadsMagic = 1.0
    pHeadsNormal = 0.5       # start with 50% chance of the magic coin, which is the same as odds = 1:1
    for i in range(n):
        r = pHeadsMagic / pHeadsNormal           # edit here to update the odds
        odds *= r
    print(odds)

n = 3
flip(n)