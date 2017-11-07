#!/usr/bin/env python
from __future__ import print_function
import unittest
import ROOT
import random
from array import array

class TestInit(unittest.TestCase):

    def test_Init(self):
        scratchDirectory = '.'

        def make_tree(fileName, numEvents=10000, offset=0):

            f = ROOT.TFile(fileName, 'recreate')
            t = ROOT.TTree('tree', 'random data tree')

            maxn = 10
            e = array('i', [0])
            a = array('f', [0])
            b = array('f', [0])
            c = array('f', [0])
            n = array('i', [0])
            d = array('f', maxn * [0.])
            useless_array = array('i', [0])
            t.Branch('event', e, 'event/I')
            t.Branch('a', a, 'a/F')
            t.Branch('b', b, 'b/F')
            t.Branch('c', c, 'c/F')
            t.Branch('nJet', n, 'nJet/I')
            t.Branch('Jet', d, 'Jet[nJet]/F')

            for i in range(100):
                t.Branch('useless_integer_%d'%i, useless_array, 'useless_integer_%d/I'%i)

            for i in range(numEvents):

                e[0] = offset + i
                n[0] = random.randint(0, maxn-1)
                for j in range(n[0]):
                    d[j] = random.uniform(20, 200 - j*10)
                a[0] = random.uniform(-1, 1)
                b[0] = random.uniform(0, 100) + 10 * random.gauss(40, 10)
                c[0] = random.gauss(0, 2)
                t.Fill()

            f.Write()
            print("written:", fileName)

        numEvents = 100000
        for i in range(10):
            make_tree(scratchDirectory + '/tree_%d.root'%i, numEvents=numEvents, offset=i*numEvents)

if __name__ == '__main__':
    unittest.main()
