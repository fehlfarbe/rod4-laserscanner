'''
Created on 08.10.2015

@author: kolbe
'''
import serial
import math
import collections
from threading import Thread, Lock
import time


class ROD4Scanner(object):
    
    MAX_ANGLE = 190
    
    __serial = None
    
    __running = False
    __thread = None
    __lock = None
    
    __values_update = time.time()
    __values_x = []
    __values_y = []
    __distances = []
    
    __avg_len = 10
    __avg_values = collections.deque(maxlen=__avg_len)
    
    __angle = 190
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=57600):
        self.__serial = serial.Serial(port, baudrate)
        
    def __read_serial(self):
        return ord(self.__serial.read())
    
    def __angle_in_range(self, angle):
        m = self.MAX_ANGLE / 2.0
        w = self.__angle / 2.0
        #print m, w, angle > (m-w), angle < (m+w)
        if angle > (m-w) and angle < (m+w):
            return True
        return False
    
    def __run(self):
        self.__running = True
        count = 0
        i3 = 0
        val = 0
        max_y = 0
        while self.__running:
            if i3 != 3:
                val = self.__read_serial()
            if val == 254:
                i3 = 0
                for a in range(0, 3):
                    val = self.__read_serial()
                    val = self.__read_serial()
                    if val == 254:
                        i3 += 1
            if i3 == 3:
                scan_res = self.__read_serial() # gibt die Scanneraufloesung an (1=sehr hoch, 8=sehr niedrig)
                multSegB = self.__read_serial() # Startsegmentmultiplikator []=0 1=256 2=512  
                segB = self.__read_serial()     # gibt an, mit welchem Segment der Scanner beginnt; Segment=MultSegB*256+SegB-1, weil 0 nicht ausgegeben wird  
                multSegE = self.__read_serial() # Endsegmentmultiplikator []=0 1=256 2=512
                segE = self.__read_serial()     # gibt an, mit welchem Segment der Scanner aufhoert; Segment=MultSegE*256+SegE-1, weil 0 nicht ausgegeben wird
                
                scan_res = float(scan_res)
                multSegB = float(multSegB)
                segB = float(segB)
                multSegE = float(multSegE)
                segE = float(segE)
                
                startSeg = multSegB * 256 + segB - 1
                endSeg = multSegE * 256 + segE - 1
                countVal = int(round(endSeg/scan_res - startSeg/scan_res + 0.5))
                
                endsegR = countVal * scan_res + startSeg #realer Wert fuer das Endsegment
                startsegDeg = 0.36 * startSeg #Anfangswert in Grad umgerechnet
                
                '''
                print "-----------------"
                print "scan res: ", scan_res
                print "segmentmultiplikator: ", multSegB
                print "segB", segB
                print "startSeg", startSeg
                print "endSeg", endSeg
                print "countVal", countVal
                print "-----------------"
                '''
                
                distances = []
                x_vals = []
                y_vals = []
                for i in range(0, countVal):
                    mult = self.__read_serial()  # multiplikator
                    v = float(self.__read_serial())  # value
                    dist = mult * 256 + v - 1
                    resolution = 0.36 * scan_res
                    angle = (i*resolution)+startsegDeg-5.0
                    if not self.__angle_in_range(angle):
                        #print angle, "not in range", self.__angle
                        continue
                    x = dist*math.cos(math.pi/180.0*angle)*-1.0 
                    y = dist*math.sin(math.pi/180.0*angle)
                    #print x, y
                    distances.append(dist)
                    x_vals.append(x)
                    y_vals.append(y)
                    #print x, y, dist
                    
                with self.__lock:
                    self.__values_x = x_vals
                    self.__values_y = y_vals
                    self.__avg_values.append((self.__values_x, self.__values_y))
                    self.__values_update = time.time()
                # get avergae
                #average.append([x_vals, y_vals])    
                #avg_x, avg_y = average.get_average()
                # plot
                #max_y = max(max_y, max(y_vals))
                #pyplot.clf()
                #pyplot.plot(x_vals, y_vals)
                #pyplot.plot(avg_x, avg_y)
                #pyplot.plot(distances)
                #pyplot.ylim([0, max_y])
                #pyplot.xlim([-300, 300])
                #pyplot.draw()
            
            #pyplot.show(block=False)
            
            #print "[%d] : %s" % (count, line)
            count += 1
        
    def __enter__(self):
        self.__thread = Thread(target=self.__run)
        self.__lock = Lock()
        self.__thread.start()
        return self
        
    def __exit__(self, t, value, tb):
        if self.__thread:
            self.__running = False
            self.__thread.join()
            
    @property
    def angle(self):
        return self.__angle
    
    @angle.setter
    def angle(self, value):
        self.__angle = min(self.MAX_ANGLE, max(5, value))
            
    def last_values(self):
        return self.__values_x, self.__values_y
    
    def values(self):
        t0 = time.time()
        while t0-self.__values_update > 0:
            time.sleep(0.01)
        return self.__values_x, self.__values_y
    
    def avg_values(self):
        avg = list(self.__avg_values)
        l = len(avg)
                
        if l == 0:
            return [], []
        
        x_vals = [0] * len(avg[0][0])
        y_vals = [0] * len(avg[0][1])
        
        for a in avg:
            for i, x in enumerate(a[0]):
                x_vals[i] += x/l
            for i, y in enumerate(a[1]):
                y_vals[i] += y/l
                
        return x_vals, y_vals