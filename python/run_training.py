#!/usr/bin/env python
from __future__ import print_function
from optparse import OptionParser
import ROOT
ROOT.gROOT.SetBatch(True)
from myutils import NewTreeCache as TreeCache
from myutils.sampleTree import SampleTree as SampleTree
from myutils import BetterConfigParser, ParseInfo
import resource
import os
import sys
import pickle
import glob
import shutil
import numpy as np

class MvaTrainingHelper(object):

    def __init__(self, config, mvaName):
        self.config = config
        self.factoryname = config.get('factory', 'factoryname')
        self.factorysettings = config.get('factory', 'factorysettings')
        self.samplesPath = config.get('Directories', 'MVAin')
        self.samplesDefinitions = config.get('Directories','samplesinfo') 
        self.samplesInfo = ParseInfo(self.samplesDefinitions, self.samplesPath)

        self.sampleFilesFolder = config.get('Directories', 'samplefiles')

        self.treeVarSet = config.get(mvaName, 'treeVarSet')
        self.MVAtype = config.get(mvaName, 'MVAtype')
        self.MVAsettingsRaw = config.get(mvaName,'MVAsettings')
        self.MVAsettings = self.MVAsettingsRaw
        self.mvaName = mvaName
        self.mvaNameRaw = mvaName

        VHbbNameSpace = config.get('VHbbNameSpace', 'library')
        ROOT.gSystem.Load(VHbbNameSpace)

        # variables
        self.MVA_Vars = {}
        self.MVA_Vars['Nominal'] = config.get(self.treeVarSet, 'Nominal').strip().split(' ')

        # samples
        backgroundSampleNames = eval(config.get(mvaName, 'backgrounds'))
        signalSampleNames = eval(config.get(mvaName, 'signals'))
        self.samples = {
            'BKG': self.samplesInfo.get_samples(backgroundSampleNames),
            'SIG': self.samplesInfo.get_samples(signalSampleNames),
        }

        self.treeCutName = config.get(mvaName, 'treeCut')
        self.treeCut = config.get('Cuts', self.treeCutName)

        try:
            self.nRuns = int(config.get(mvaName, 'nRuns'))
        except:
            self.nRuns = 1
        self.TrainCut = config.get('Cuts', 'TrainCut') 
        self.EvalCut = config.get('Cuts', 'EvalCut')
        print("TRAINING CUT:", self.TrainCut)
        print("EVAL CUT:", self.EvalCut)

        self.globalRescale = 2.0
        
        self.trainingOutputFileName = 'mvatraining_{factoryname}_{region}.root'.format(factoryname=self.factoryname, region=mvaName)
        self.trainingOutputFile = ROOT.TFile.Open(self.trainingOutputFileName, "RECREATE")

        # ----------------------------------------------------------------------------------------------------------------------
        # create TMVA factory
        # ----------------------------------------------------------------------------------------------------------------------
        self.factory = ROOT.TMVA.Factory(self.factoryname, self.trainingOutputFile, self.factorysettings)
        if self.trainingOutputFile and self.factory:
            print ("INFO: initialized MvaTrainingHelper.", self.factory) 
        else:
            print ("\x1b[31mERROR: initialization of MvaTrainingHelper failed!\x1b[0m") 


    def evalMvaSettings(self):

        if 'np.random' in self.MVAsettingsRaw:
            settings = self.MVAsettingsRaw.split(':')
            for i in range(len(settings)):
                val = settings[i].split('=')
                if len(val) > 1:
                    val[1]=str(eval(val[1].strip()))
                settings[i] = "=".join(val)
                self.MVAsettings = ":".join(settings)
            self.mvaName = self.mvaNameRaw + hex(hash(self.MVAsettings))[2:]
        return self

    def prepare(self):
        # ----------------------------------------------------------------------------------------------------------------------
        # add sig/bkg x training/eval trees
        # ----------------------------------------------------------------------------------------------------------------------
        try:
            addBackgroundTreeMethod = self.factory.AddBackgroundTree
            addSignalTreeMethod = self.factory.AddSignalTree
            self.dataLoader = None
        except:
            print("oh no..")
            # the DataLoader wants to be called '.'
            self.dataLoader = ROOT.TMVA.DataLoader(".")
            addBackgroundTreeMethod = self.dataLoader.AddBackgroundTree
            addSignalTreeMethod = self.dataLoader.AddSignalTree

        self.sampleTrees = []
        for addTreeFcn, samples in [
                    [addBackgroundTreeMethod, self.samples['BKG']],
                    [addSignalTreeMethod, self.samples['SIG']]
                ]:
            for sample in samples:
                print ('*'*80,'\n%s\n'%sample,'*'*80)
                for additionalCut in [self.TrainCut, self.EvalCut]:
                    # cuts
                    sampleCuts = [sample.subcut]
                    if additionalCut:
                        sampleCuts.append(additionalCut)
                    # cut from the mva region
                    if self.treeCut:
                        sampleCuts.append(self.treeCut)

                    tc = TreeCache.TreeCache(
                            sample=sample,
                            cutList=sampleCuts,
                            inputFolder=self.samplesPath,
                            config=self.config,
                            debug=True
                        )
                    sampleTree = tc.getTree()
                    self.sampleTrees.append(sampleTree)
                    if sampleTree:
                        treeScale = sampleTree.getScale(sample) * self.globalRescale
                        if sampleTree.tree.GetEntries() > 0:
                            addTreeFcn(sampleTree.tree, treeScale, ROOT.TMVA.Types.kTraining if additionalCut == self.TrainCut else ROOT.TMVA.Types.kTesting)
                    else:
                        print ("\x1b[31mERROR: TREE NOT FOUND:", sample.name, " -> not cached??\x1b[0m")
                        raise Exception("CachedTreeMissing")

        if self.dataLoader:
            for var in self.MVA_Vars['Nominal']:
                self.dataLoader.AddVariable(var, 'D')
        else:
            for var in self.MVA_Vars['Nominal']:
                self.factory.AddVariable(var, 'D')

        return self

    # ----------------------------------------------------------------------------------------------------------------------
    # backup old .xml and .info files 
    # ----------------------------------------------------------------------------------------------------------------------
    def backupOldFiles(self):
        success = False
        MVAdir = self.config.get('Directories','vhbbpath')+'/python/weights/'
        backupDir = MVAdir + 'backup/'
        try:
            os.makedirs(backupDir)
        except:
            pass
        freeNumber = 1
        try:
            lastUsedBackupDirectories = sorted(glob.glob(backupDir + '/v*/'), key=lambda x: int(x.strip('/').split('/')[-1][1:]), reverse=True)
            freeNumber = 1 + int(lastUsedBackupDirectories[0].strip('/').split('/')[-1][1:]) if len(lastUsedBackupDirectories) > 0 else 1
        except Exception as e:
            print("\x1b[31mERROR: creating backup of MVA files failed!", e, "\x1b[0m")
            freeNumber = -1
        if freeNumber > -1:
            try:
                fileNamesToBackup = glob.glob(MVAdir + self.factoryname+'_'+self.mvaName + '.*')
                fileNamesToBackup += glob.glob(MVAdir + '/../mvatraining_MVA_ZllBDT_*.root')
                os.makedirs(backupDir + 'v%d/'%freeNumber)
                for fileNameToBackup in fileNamesToBackup:
                    shutil.copy(fileNameToBackup, backupDir + 'v%d/'%freeNumber)
                success = True
            except Exception as e:
                print("\x1b[31mERROR: creating backup of MVA files failed!", e, "\x1b[0m")
        return success


    def book(self):
        #print('backing up old BDT files')
        #self.backupOldFiles()
        # ----------------------------------------------------------------------------------------------------------------------
        # Execute TMVA
        # ----------------------------------------------------------------------------------------------------------------------
        self.factory.Verbose()
        print('Execute TMVA: factory.BookMethod("%s", "%s", "%s")'%(self.MVAtype, self.mvaName, self.MVAsettings))
        weightF = self.config.get('Weights','weightF')
        try:
            self.factory.BookMethod(self.MVAtype, self.mvaName, self.MVAsettings)
            print("ROOT 5 style TMVA found")
            self.factory.SetSignalWeightExpression(weightF)
            self.factory.SetBackgroundWeightExpression(weightF)
        except:
            print("ROOT 6 style TMVA found, using data loader object!!! >_<")
            print(" weights dir:", ROOT.TMVA.gConfig().GetIONames().fWeightFileDir)
            print(" data loader:", self.dataLoader)
            print(" type:       ", self.MVAtype)
            print(" name:       ", self.mvaName)
            print(" settings:   ", self.MVAsettings)
            ROOT.TMVA.gConfig().GetIONames().fWeightFileDir = 'weights'
            self.dataLoader.SetSignalWeightExpression(weightF)
            self.dataLoader.SetBackgroundWeightExpression(weightF)
            self.factory.BookMethod(self.dataLoader, self.MVAtype, self.mvaName, self.MVAsettings)
        return self

    def run(self):
        print('Execute TMVA: TrainAllMethods')
        print('max mem used = %d'%(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        self.factory.TrainAllMethods()
        print('Execute TMVA: TestAllMethods')
        print('max mem used = %d'%(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        self.factory.TestAllMethods()
        print('Execute TMVA: EvaluateAllMethods')
        print('max mem used = %d'%(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        self.factory.EvaluateAllMethods()
        print('Execute TMVA: output.Write')
        print('max mem used = %d'%(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        self.trainingOutputFile.Close()
        return self

    def printInfo(self):
        #WRITE INFOFILE
        MVAdir = self.config.get('Directories','vhbbpath')+'/python/weights/'
        infofile = open(MVAdir+self.factoryname+'_'+self.mvaName+'.info','w')
        print ('@DEBUG: output infofile name')
        print (infofile)

        info=mvainfo(self.mvaName)
        info.factoryname=self.factoryname
        info.factorysettings=self.factorysettings
        info.MVAtype=self.MVAtype
        info.MVAsettings=self.MVAsettings
        info.weightfilepath=MVAdir
        info.path=self.samplesPath
        info.varset=self.treeVarSet
        info.vars=self.MVA_Vars['Nominal']
        pickle.dump(info,infofile)
        infofile.close()

# read arguments
argv = sys.argv
parser = OptionParser()
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                          help="Verbose mode.")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
parser.add_option("-t","--trainingRegions", dest="trainingRegions", default='',
                      help="cut region identifier")
(opts, args) = parser.parse_args(argv)
if opts.config =="":
        opts.config = ["config"]

# Import after configure to get help message
from myutils import BetterConfigParser, mvainfo, ParseInfo

# load config
config = BetterConfigParser()
config.read(opts.config)

# initialize
trainingRegions = opts.trainingRegions.split(',')
if len(trainingRegions) > 1:
    print ("ERROR: not implemented!")
    exit(1)
for trainingRegion in trainingRegions:
    th = MvaTrainingHelper(config=config, mvaName=trainingRegion)
    th.evalMvaSettings()
    print(th.MVAsettings)
    th.prepare()
    for i in range(th.nRuns):
        th.evalMvaSettings().book().printInfo()
    th.run()

