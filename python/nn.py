# Neighbour.py
''' To find the closest neighbour, in a neghbourhood P,
     to a point p.
     '''
import math
import numarray as N
import numarray.numerictypes as _nt
import numarray.random_array as R

trial= 0
lengthRemaining= []
def find(P, p):
   ''' In the 2D neighbourhood P, find the point closest to p.
      The approach is based on the selection of a trial value Pt, from 
P, and
      discarding all values further than Pt from p.
      To avoid repeated sqrt calculations the discard is based on an
      enclosing square.
      '''
   global lengthRemaining, trial
   lengthRemaining+= [[P.shape[0]]]
   Pz= P - p                             # zero based neighbourhood
   while len(Pz):
     Pt= Pz[0]                           # trial value
     Pta= N.abs(Pt)
     Pz= Pz[1:]
     pd= math.sqrt(N.dot(Pta, Pta))      # distance of p from the trial 
value
     goodCases= N.logical_and((Pz < pd),
                              (Pz > -pd))# use the enclosing square
     goodCases= N.logical_and.reduce(goodCases, 1)
     Pz= N.compress(goodCases, Pz)  # discard points outside the square
     if len(Pz) == 1:
       Pt= Pz[0]                         # We have found the closest
       Pz= []
     lengthRemaining[trial]+= [len(Pz)]
     z= 100
   trial+= 1
   return Pt + p

if __name__ == '__main__':
   for sampleSize in range(100, 5000, 100):
     P= R.random(shape= (sampleSize, 2))
     for i in range(20):
       p= R.random((1, 2))                   # point
       a= find(P, p)
##      print 'Closest neighbour:', a[0]
##      print 'Check - Point(p):', p[0]
   ##  check= []
   ##  for i in range(len(P)):
   ##    check+= [(math.sqrt((P[i, 0]-p[0, 0])**2 + (P[i, 1]-p[0,1])**2), P[i, 0], P[i, 1])]
   ##    print P[i], math.sqrt((P[i, 0]-p[0, 0])**2 + (P[i, 1]-p[0, 1])**2)
   ##  check.sort()
   ##  print check[0]
   ##  print check
     print 'Number of scans:', sum([len(lst) for lst in lengthRemaining])
     print 'Sample size:', P.shape[0], ' Average numner of scans:', 
sum([len(lst) for lst in lengthRemaining])/float(len(lengthRemaining))
