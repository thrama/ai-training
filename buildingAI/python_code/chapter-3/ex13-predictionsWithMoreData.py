# Try modifying the code below by adding the numbers for a sixth cabin into the data so that you have the following data set. Do not change the print statements.
#
# cabin 1	25	2	50	1	500	    127,900
# cabin 2	39	3	10	1	1000    222,100
# cabin 3	13	2	13	1	1000    143,750
# cabin 4	82	5	20	2	120	    268,000
# cabin 5	130	6	10	2	600	    460,700
# cabin 6	115	6	10	1	550	    407,000

import numpy as np

def main():
    np.set_printoptions(precision=1)

    x = np.array(
        [
            [25, 2, 50, 1, 500], 
            [39, 3, 10, 1, 1000], 
            [13, 2, 13, 1, 1000], 
            [82, 5, 20, 2, 120], 
            [130, 6, 10, 2, 600],
            [115, 6, 10, 1, 550]
        ]
    )   

    y = np.array([127900, 222100, 143750, 268000, 460700, 407000])

    c = np.linalg.lstsq(x, y)[0]
    print(c)

    print(x @ c)

main()