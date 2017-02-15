# -*- coding: utf-8 -*-
'''
Created on 08.10.2015

@author: kolbe
'''
from optparse import OptionParser
from matplotlib import pyplot
from ROD4Scanner import ROD4Scanner


if __name__ == '__main__':
    
    parser = OptionParser()
    parser.add_option("-s", "--show", dest="show",
                  help="Show window", default=True, action="store_true")
    parser.add_option("--min", dest="min",
                  help="Minimum distance in mm", default=150)
    parser.add_option("--max", dest="max",
                  help="Maximum distance in mm", default=4000)
    parser.add_option("--angle", dest="angle",
                  help="Angle in degree", default=75)
    (options, args) = parser.parse_args()
    
    with ROD4Scanner() as scanner:
        while True:
            try:
                x, y = scanner.values()
                pyplot.clf()
                pyplot.plot(x, y, c='r')
                pyplot.pause(0.001)
                print(x)
                print(y)
            except KeyboardInterrupt:
                break
