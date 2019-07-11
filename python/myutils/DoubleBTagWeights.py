#!/usr/bin/env python
import ROOT
import sys
import numpy as np

class DoubleBTagWeights(object):

    def __init__(self):
        self.branchBuffers = {}
        self.branches = []

        self.bname = [
                'DoubleBLWeight',
                'DoubleBM1Weight',
                'DoubleBM2Weight',
                'DoubleBTWeight',
                'DoubleBLWeightUp',
                'DoubleBM1WeightUp',
                'DoubleBM2WeightUp',
                'DoubleBTWeightUp',
                'DoubleBLWeightDown',
                'DoubleBM1WeightDown',
                'DoubleBM2WeightDown',
                'DoubleBTWeightDown',
                ]

        for b in self.bname:
            self.branchBuffers[b] = np.ones(6, dtype=np.float32) #all Fat jets (6 in total)
            self.branches.append({'name': b, 'formula': self.getVectorBranch, 'arguments': {'branch': b, 'length':6}, 'length': 6})

    def getVectorBranch(self, event, arguments=None, destinationArray=None):
        self.processEvent(event)
        for i in range(arguments['length']):
            destinationArray[i] =  self.branchBuffers[arguments['branch']][i]

    def getBranches(self):
        return self.branches

    def processEvent(self, tree):

        #Fill the double b tagger
        for i in range(min(tree.nFatjetAK08ungroomed,6)):
            DoubleB  = self.getBBtagSF(tree.FatjetAK08ungroomed_pt[i])
            index_ = 0
            for b in self.bname:
                self.branchBuffers[b][i] = DoubleB[index_]
                index_ += 1
        for i in range(tree.nFatjetAK08ungroomed, 6):
            for b in self.bname:
                self.branchBuffers[b][i] = 1.0

        return True

    #def getBBtagSF(self, Wp, pt):
    def getBBtagSF(self, pt):
        index = -1
        if pt < 350:
            index = 0
        elif pt > 350 and pt < 430:
            index = 1
        elif pt > 430:
            index = 2

        #if 'DoubleBLWeight' in Wp:
        SFL = [[0.96, 1., 1.01], [0.99, 1.04, 1.03], [0.94, 0.97, 0.97]]
        #elif 'DoubleBM1Weight' in Wp:
        SFM1 = [[0.93, 1.01, 0.99], [0.96, 1.04, 1.01], [0.91, 0.98, 0.95]]
        #elif 'DoubleBM2Weight' in Wp:
        SFM2 = [[0.92, 1.01, 0.92], [0.95, 1.04, 0.95], [0.89, 0.97, 0.87]]
        #elif 'DoubleBTWeight' in Wp:
        SFT = [[0.85, 0.91, 0.91], [0.88, 0.94, 0.94], [0.82, 0.87, 0.87]]

        Nom     = [SFL[0][index], SFM1[0][index], SFM2[0][index], SFT[0][index]]
        Up      = [SFL[1][index], SFM1[1][index], SFM2[1][index], SFT[1][index]]
        Down    = [SFL[2][index], SFM1[2][index], SFM2[2][index], SFT[2][index]]

        return Nom+Up+Down

        #return SF[indexsys][index]


