#!/usr/bin/env python
from myutils import ParseInfo

class SampleGroup(object):

    def __init__(self, groupDict=None, prefix="is_", eventCounts=None):
        self.groupDict = groupDict
        self.prefix = prefix
        if eventCounts:
            with open(eventCounts, 'r') as inFile:
                self.eventCountsDict = eval(inFile.read())
        else:
            self.eventCountsDict = None

        self.branches = []
        self.eventNumberOffset = 0L

    def customInit(self, initVars):
        self.sample = initVars['sample']
        self.sampleTree = initVars['sampleTree']
        self.config = initVars['config']
        self.samplesDefinitions = self.config.get('Directories','samplesinfo') 
        self.samplesInfo = ParseInfo(self.config.get('Directories','samplesinfo'), self.config.get('Directories', 'dcSamples'))
        self.subsamples = [x for x in self.samplesInfo if x.identifier == self.sample.identifier and x.subsample]
        for s in self.subsamples:
            print s.name, s.subcut
            self.sampleTree.addFormula(s.subcut)

        if not self.groupDict:
            self.groupDict = eval(self.config.get('LimitGeneral','Group'))
        
        self.groupNames = list(set(self.groupDict.values()))
        self.groups = {k: [x for x,y in self.groupDict.iteritems() if y==k] for k in self.groupNames}

        for groupName, sampleNames in self.groups.iteritems():
            self.branches.append({'name': self.prefix + groupName, 'formula': self.isInGroup, 'arguments': groupName}) 

        self.branches.append({'name': 'sampleIndex', 'formula': self.getSampleIndex, 'type': 'i'})

        if self.eventCountsDict:
            self.branches.append({'name': 'event_unique', 'formula': self.getEventNumber, 'type': 'l'})
            
            if len(self.sampleTree.sampleFileNames) != 1:
                print("ERROR: adding unique event numbers for chains is not implemented!")
                raise Exception("SampleGroup__customInit__not_implemented")
            self.eventNumberOffset = self.eventCountsDict[self.sample.identifier][self.sampleTree.sampleFileNames[0]]

    def getBranches(self):
        return self.branches

    def isInGroup(self, event, arguments):
        groupName = arguments
        if len(self.subsamples) > 0:
            for s in self.subsamples:
                if self.sampleTree.evaluate(s.subcut):
                    return s.name in self.groups[groupName]
        else:
            return self.sample.name in self.groups[groupName]
    
    def getSampleIndex(self, event):
        if len(self.subsamples) > 0:
            for s in self.subsamples:
                if self.sampleTree.evaluate(s.subcut):
                    return s.index 
        else:
            return self.sample.index
    
    def getEventNumber(self, event):
        return self.eventNumberOffset + event.GetReadEntry()
