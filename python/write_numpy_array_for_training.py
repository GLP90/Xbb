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
import math
from copy import deepcopy
import gzip
import h5py
import json
import datetime

class SampleTreesToNumpyConverter(object):

    def __init__(self, config, mvaName, useSyst=True, useWeightSyst=True, testRun=False):
        self.mvaName = mvaName
        VHbbNameSpace = config.get('VHbbNameSpace', 'library')
        ROOT.gSystem.Load(VHbbNameSpace)
        self.dataFormatVersion = 3
        self.sampleTrees = []
        self.config = config
        self.testRun = testRun
        self.samplesPath = config.get('Directories', 'MVAin')
        self.samplesDefinitions = config.get('Directories','samplesinfo')
        self.samplesInfo = ParseInfo(self.samplesDefinitions, self.samplesPath)

        # region
        self.treeCutName = config.get(mvaName, 'treeCut')
        self.treeCut = config.get('Cuts', self.treeCutName)

        # split in train/eval sets
        self.trainCut = config.get('Cuts', 'TrainCut') 
        self.evalCut = config.get('Cuts', 'EvalCut')
        
        # rescale MC by 2 because of train/eval split
        self.globalRescale = 2.0

        # variables and systematics
        self.treeVarSet = config.get(mvaName, 'treeVarSet')
        self.MVA_Vars = {'Nominal': [x for x in config.get(self.treeVarSet, 'Nominal').strip().split(' ') if len(x.strip()) > 0]}

        self.weightSYS = []
        self.weightSYSweights = {}

        self.systematics = []
        if useSyst:
            print('INFO: use systematics in training!')
            self.systList = eval(self.config.get(mvaName, 'systematics')) if self.config.has_option(mvaName, 'systematics') else []
            for syst in self.systList:
                systNameUp   = syst+'_UP'   if self.config.has_option('Weights',syst+'_UP')   else syst+'_Up'
                systNameDown = syst+'_DOWN' if self.config.has_option('Weights',syst+'_DOWN') else syst+'_Down'

                self.systematics.append({
                    'name': syst,
                    'U': self.config.get('Weights', systNameUp),
                    'D': self.config.get('Weights', systNameDown),
                    })

        # default: signal vs. background
        self.sampleNames = {
                    'SIG_ALL': eval(self.config.get('Plot_general', 'allSIG')),
                    'BKG_ALL': eval(self.config.get('Plot_general', 'allBKG')),
                }
        # for multi-output classifiers load dictionary from config
        if self.config.has_option(mvaName, 'classDict'):
            self.sampleNames = eval(self.config.get(mvaName, 'classDict'))
            print("classes dict:", self.sampleNames)
        self.samples = {category: self.samplesInfo.get_samples(samples) for category,samples in self.sampleNames.iteritems()}
        if self.testRun:
            print("\x1b[31mDEBUG: TEST-RUN, using only small subset of samples!\x1b[0m")


    def run(self):
        # ----------------------------------------------------------------------------------------------------------------------
        # add sig/bkg x training/testing trees
        # ----------------------------------------------------------------------------------------------------------------------
        categories = self.samples.keys()
        datasetParts = {'train': self.trainCut, 'test': self.evalCut}

        systematics = self.systematics
        arrayLists = {datasetName:[] for datasetName in datasetParts.iterkeys()}
        #arrayLists_sys = {x: {datasetName:[] for datasetName in datasetParts.iterkeys()} for x in systematics}
        weightLists = {datasetName:[] for datasetName in datasetParts.iterkeys()}
        targetLists = {datasetName:[] for datasetName in datasetParts.iterkeys()}

        weightListsSYS = {x: {datasetName:[] for datasetName in datasetParts.iterkeys()} for x in self.weightSYS} 
        
        # standard weight expression
        weightF = self.config.get('Weights','weightF')

        weightListSYStotal = {datasetName:[] for datasetName in datasetParts.iterkeys()}

        for category in categories:
            if self.testRun:
                self.samples[category] = self.samples[category][0:1]
            for sample in self.samples[category]:
                print ('*'*80,'\n%s\n'%sample,'*'*80)
                for datasetName, additionalCut in datasetParts.iteritems():
                    # cuts
                    sampleCuts = [sample.subcut]
                    if additionalCut:
                        sampleCuts.append(additionalCut)
                    # cut from the mva region
                    if self.treeCut:
                        sampleCuts.append(self.treeCut)

                    # get ROOT tree for selected sample & region cut
                    tc = TreeCache.TreeCache(
                            sample=sample,
                            cutList=sampleCuts,
                            inputFolder=self.samplesPath,
                            config=self.config,
                            debug=True
                        )
                    sampleTree = tc.getTree()
                    if sampleTree:
                        treeScale = sampleTree.getScale(sample) * self.globalRescale
                        print ('scale:', treeScale)
                        
                        # initialize numpy array
                        nSamples = sampleTree.GetEntries()
                        features = self.MVA_Vars['Nominal']
                        #features_sys = {x: self.MVA_Vars[x] for x in systematics} 
                        nFeatures = len(features) 
                        print('nFeatures:', nFeatures)
                        inputData = np.zeros((nSamples, nFeatures), dtype=np.float32)
                        #inputData_sys = {x: np.zeros((nSamples, nFeatures), dtype=np.float32) for x in systematics}

                        # initialize formulas for ROOT tree
                        for feature in features:
                            sampleTree.addFormula(feature)
                        #for k, features_s in features_sys.iteritems():
                        #    for feature in features_s:
                        #        sampleTree.addFormula(feature)
                        sampleTree.addFormula(weightF)
                        #for syst in self.weightSYS:
                        #    sampleTree.addFormula(self.weightSYSweights[syst])
                        for syst in self.systematics:
                            sampleTree.addFormula(syst['U'])
                            sampleTree.addFormula(syst['D'])

                        useSpecialWeight = self.config.has_option('Weights', 'useSpecialWeight') and eval(self.config.get('Weights', 'useSpecialWeight')) 
                        if useSpecialWeight:
                            sampleTree.addFormula(sample.specialweight)

                        # fill numpy array from ROOT tree
                        for i, event in enumerate(sampleTree):
                            for j, feature in enumerate(features):
                                inputData[i, j] = sampleTree.evaluate(feature)
                            # total weight comes from weightF (btag, lepton sf, ...) and treeScale to scale MC to x-section
                            eventWeight = sampleTree.evaluate(weightF)
                            specialWeight =  sampleTree.evaluate(sample.specialweight) if useSpecialWeight else 1.0 
                            totalWeight = treeScale * eventWeight * specialWeight 
                            weightLists[datasetName].append(totalWeight)
                            targetLists[datasetName].append(categories.index(category))
                            
                            # add weights varied by (btag) systematics
                            #for syst in self.weightSYS:
                            #    weightListsSYS[syst][datasetName].append(treeScale * sampleTree.evaluate(self.weightSYSweights[syst]))
                            deltas = []
                            for syst in self.systematics:
                                delta_up   = sampleTree.evaluate(syst['U']) - eventWeight
                                delta_down = sampleTree.evaluate(syst['D']) - eventWeight
                                delta = 0.5 * (np.abs(delta_up) + np.abs(delta_down))
                                deltas.append(delta*delta)
                            totalDelta = np.sqrt(sum(deltas))

                            # convert to absolute error on total event weight
                            weightListSYStotal[datasetName].append(treeScale * totalDelta * specialWeight)

                            # fill systematics 
                            #for k, feature_s in features_sys.iteritems():
                            #    for j, feature in enumerate(feature_s):
                            #        inputData_sys[k][i,j] = sampleTree.evaluate(feature)

                        arrayLists[datasetName].append(inputData)
                        #for sys in systematics:
                        #    arrayLists_sys[sys][datasetName].append(inputData_sys[sys])

                    else:
                        print ("\x1b[31mERROR: TREE NOT FOUND:", sample.name, " -> not cached??\x1b[0m")
                        raise Exception("CachedTreeMissing")

        ##systematics for training
        #puresystematics = deepcopy(systematics)
        #if 'Nominal' in puresystematics:
        #    puresystematics.remove('Nominal')
        puresystematics = [x['name'] for x in self.systematics]

        # concatenate all data from different samples
        self.data = {
                'train': {
                    'X': np.concatenate(arrayLists['train'], axis=0),
                    'y': np.array(targetLists['train'], dtype=np.float32),
                    'sample_weight': np.array(weightLists['train'], dtype=np.float32),
                    'sample_weight_error': np.array(weightListSYStotal['train'], dtype=np.float32),
                    },
                'test': {
                    'X': np.concatenate(arrayLists['test'], axis=0), 
                    'y': np.array(targetLists['test'], dtype=np.float32), 
                    'sample_weight': np.array(weightLists['test'], dtype=np.float32),
                    'sample_weight_error': np.array(weightListSYStotal['test'], dtype=np.float32),
                    },
                'category_labels': {idx: label for idx, label in enumerate(categories)},
                'meta': {
                    'version': self.dataFormatVersion,
                    'region': self.mvaName,
                    'cutName': self.treeCutName,
                    'cut': self.treeCut,
                    'trainCut': self.trainCut,
                    'testCut': self.evalCut,
                    'samples': self.sampleNames,
                    'weightF': weightF,
                    'weightSYS': self.weightSYS,
                    'variables': ' '.join(self.MVA_Vars['Nominal']),
                    'systematics': puresystematics,
                    }
                }
        ## add systematics variations
        #for sys in systematics:
        #    self.data['train']['X_'+sys] = np.concatenate(arrayLists_sys[sys]['train'], axis=0)
        #for syst in self.weightSYS:
        #    self.data['train']['sample_weight_'+syst] = np.array(weightListsSYS[syst]['train'], dtype=np.float32)

        if not os.path.exists("./dumps"):
            os.makedirs("dumps")
        baseName = './dumps/' +self.config.get("Directories","Dname").split("_")[1] + '_' + self.mvaName + '_' + datetime.datetime.now().strftime("%y%m%d")
        numpyOutputFileName = baseName + '.dmpz'
        hdf5OutputFileName = baseName + '.h5'
        print("INFO: saving output...")
        
        try:
            self.saveAsPickledNumpy(numpyOutputFileName)
        except Exception as e:
            print(e)

        try:
            self.saveAsHDF5(hdf5OutputFileName)
        except Exception as e:
            print(e)
        print("INFO: done.")

    def saveAsPickledNumpy(self, outputFileName):
        with gzip.open(outputFileName, 'wb') as outputFile:
            pickle.dump(self.data, outputFile)
        print("written to:\x1b[34m", outputFileName, " \x1b[0m")

    def saveAsHDF5(self, outputFileName):
        f = h5py.File(outputFileName, 'w')
        for k in ['meta', 'category_labels']:
            f.attrs[k] = json.dumps(self.data[k].items())
        for k in ['train', 'test']:
            for k2 in self.data[k].keys():
                f.create_dataset(k + '/' + k2, data=self.data[k][k2], compression="gzip", compression_opts=9)
        f.close()
        print("written to:\x1b[34m", outputFileName, " \x1b[0m")


# read arguments
argv = sys.argv
parser = OptionParser()
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
parser.add_option("-T", "--tag", dest="tag", default='',
                      help="configuration tag")
parser.add_option("-t","--trainingRegions", dest="trainingRegions", default='',
                      help="cut region identifier")
parser.add_option("-S","--systematics", dest="systematics", default=2,
                      help="include systematics (0 for none, 1 for bdtVars, 2 for all (with btagWeights)")
parser.add_option("-x", "--test", dest="test", action="store_true", help="for debugging only!!!", default=False)
(opts, args) = parser.parse_args(argv)
if opts.config =="":
        opts.config = ["config"]

# Import after configure to get help message
from myutils import BetterConfigParser, mvainfo, ParseInfo

if len(opts.tag.strip()) > 1:
    config = BetterConfigParser()
    config.read("{tag}config/paths.ini".format(tag=opts.tag))
    configFiles = config.get("Configuration", "List").split(' ')
    opts.config = ["{tag}config/{file}".format(tag=opts.tag, file=x.strip()) for x in configFiles]
    print("reading config files:", opts.config)

sys = False
btagSys = False
if int(opts.systematics) > 0:
    sys = True
    if int(opts.systematics) > 1:
        btagSys = True
# load config
config = BetterConfigParser()
config.read(opts.config)
converter = SampleTreesToNumpyConverter(config, opts.trainingRegions, useSyst=sys, useWeightSyst=btagSys, testRun=opts.test)
converter.run()
