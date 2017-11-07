from __future__ import print_function
import ROOT
import TdrStyles

from NewTreeCache import TreeCache as TreeCache
from sampleTree import SampleTree

class NewHistoMaker:

    instanceCounter = 0

    def __init__(self, config, sample, sampleTree, histogramOptions):
        NewHistoMaker.instanceCounter += 1
        self.config = config
        self.sample = sample
        self.sampleTree = sampleTree
        self.histogramOptions = histogramOptions
        self.histogram = None
        TdrStyles.tdrStyle()

    def initializeHistogram(self):
        self.histogramName = (self.histogramOptions['name']+'_') if 'name' in self.histogramOptions else ''
        self.histogramName += self.sample.name + '_' + self.histogramOptions['var']
        # add unique instance counter to avoid same name for histogram and ROOT complaining
        if 'uniqueid' in self.histogramOptions and self.histogramOptions['uniqueid']:
            self.histogramName += '_instance%d'%NewHistoMaker.instanceCounter
        self.histogram = ROOT.TH1F(self.histogramName, self.histogramName, self.histogramOptions['nBins'], self.histogramOptions['xMin'], self.histogramOptions['xMax'])
        self.histogram.Sumw2()
        self.histogram.SetTitle(self.sample.name)
        return self.histogram

    def scaleHistogram(self):
        if self.sample.type != 'DATA':
            ScaleFactor = self.sampleTree.getScale(self.sample)
            if ScaleFactor != 0:
                self.histogram.Scale(ScaleFactor)
            else:
                print ("\x1b[31mWARNING: histogram scaling factor is 0!\x1b[0m")

    def getHistogram(self, cut='1'):
        if self.initializeHistogram():
            # apply weights only to MC and not to DATA
            if 'group' in self.histogramOptions and self.histogramOptions['group'] == 'DATA':
                weightF = '1'
            else:
                weightF = "({weight})".format(weight=self.histogramOptions['weight'] if ('weight' in self.histogramOptions and self.histogramOptions['weight']) else '1') 

            # add tree cut 
            # TODO: add sample cut again, which should not matter but to be safe
            selection = "({weight})*({cut})".format(weight=weightF, cut=cut) 
            nEvents = self.sampleTree.tree.Draw('{var}>>{histogramName}'.format(var=self.histogramOptions['treeVar'], histogramName=self.histogramName), selection)
            if nEvents < 0:
                print ("\x1b[31mERROR: error in TTree:Draw! returned {nEvents}\x1b[0m".format(nEvents=nEvents))
            self.scaleHistogram()
        else:
            print ("ERROR: initialization of histogram failed!")
            raise Exception("HistoMakerInitializationError")

        if 'addOverFlow' in self.histogramOptions and self.histogramOptions['addOverFlow']:
            uFlow = self.histogram.GetBinContent(0)+self.histogram.GetBinContent(1)
            oFlow = self.histogram.GetBinContent(self.histogram.GetNbinsX()+1)+self.histogram.GetBinContent(self.histogram.GetNbinsX())
            uFlowErr = ROOT.TMath.Sqrt(ROOT.TMath.Power(self.histogram.GetBinError(0),2)+ROOT.TMath.Power(self.histogram.GetBinError(1),2))
            oFlowErr = ROOT.TMath.Sqrt(ROOT.TMath.Power(self.histogram.GetBinError(self.histogram.GetNbinsX()),2)+ROOT.TMath.Power(self.histogram.GetBinError(self.histogram.GetNbinsX()+1),2))
            self.histogram.SetBinContent(1,uFlow)
            self.histogram.SetBinContent(self.histogram.GetNbinsX(),oFlow)
            self.histogram.SetBinError(1,uFlowErr)
            self.histogram.SetBinError(self.histogram.GetNbinsX(),oFlowErr)

        return self.histogram

