from __future__ import print_function
import ROOT 
ROOT.gROOT.SetBatch(True)
import TdrStyles
import os
import array
import time
import subprocess
import math

from Ratio import getRatio
from NewHistoMaker import NewHistoMaker as HistoMaker
from sampleTree import SampleTree as SampleTree

# ------------------------------------------------------------------------------
# produces histograms from trees with HistoMaker, groups them, and draws a
# stacked histogram
# ------------------------------------------------------------------------------
class NewStackMaker:
    def __init__(self, config, var, region, SignalRegion, setup=None, subcut='', title=None):
        self.debug = 'XBBDEBUG' in os.environ
        self.config = config
        self.saveShapes = True
        self.var = var
        self.region = region
        if self.config.has_section('Plot:%s'%region):
            self.configSection = 'Plot:%s'%region
        elif self.config.has_section('Fit:%s'%region):
            self.configSection = 'Fit:%s'%region
        else:
            print("ERROR: no section '%s'"%('Plot:%s'%region))
            raise Exception("ConfigError")

        self.dataGroupName = 'DATA'
        self.anaTag = self.config.get("Analysis", "tag")
        self.subcut = subcut
        self.forceLog = None
        self.normalize = eval(self.config.get(self.configSection, 'Normalize')) if self.config.has_option(self.configSection, 'Normalize') else False
        self.log = eval(self.config.get(self.configSection, 'log')) if self.config.has_option(self.configSection, 'log') else False
        self.mcUncertaintyLegend = eval(self.config.get('Plot_general','mcUncertaintyLegend')) if self.config.has_option('Plot_general','mcUncertaintyLegend') else "MC uncert. (stat.)"
        if self.config.has_option('plotDef:%s'%var, 'log'):
            self.log = eval(self.config.get('plotDef:%s'%var,'log'))
        self.blind = eval(self.config.get(self.configSection,'blind')) if self.config.has_option(self.configSection,'blind') else False
        self.xAxis = self.config.get('plotDef:%s'%self.var,'xAxis')
        self.yAxis = self.config.get('plotDef:%s'%self.var,'yAxis') if self.config.has_option('plotDef:%s'%self.var,'yAxis') else None
        self.is2D = True if self.yAxis else False
        self.typLegendDict = eval(config.get('Plot_general','typLegendDict'))
        self.plotLabels = {}
        if setup is None:
            self.setup = [x.strip() for x in self.config.get('Plot_general', 'setupLog' if self.log else 'setup').split(',') if len(x.strip()) > 0]
        else:
            self.setup = setup
        if not title:
            if self.config.has_option('Plot_general', 'title'):
                title = eval(self.config.get('Plot_general', 'title'))

        self.plotTitle = title if title else "CMS"

        self.rebin = 1
        self.histogramOptions = {
                'rebin': 1,
                'var': self.var,
                }
        self.additionalTextLines = [""]
        if self.config.has_option('Plot_general', 'additionalText'):
            self.additionalTextLines = eval(self.config.get('Plot_general', 'additionalText'))
            if self.config.has_option(self.configSection, 'additionalText'):
                aText = eval(self.config.get(self.configSection, 'additionalText'))
                if type(aText) == list:
                    self.additionalTextLines += aText
                else:
                    self.additionalTextLines.append(aText)

        # general event by event weight which is applied to all samples
        #  for special plots of weights itself, weightF can be defined in the plot definition
        if self.config.has_option('plotDef:%s'%self.var,'weightF'):
            self.histogramOptions['weight'] = self.config.get('plotDef:%s'%self.var,'weightF')
        elif self.config.has_option('plotDef:%s'%self.var,'weight'):
            self.histogramOptions['weight'] = self.config.get('plotDef:%s'%self.var,'weight')
        elif self.config.has_option('Weights','weightF'):
            self.histogramOptions['weight'] = self.config.get('Weights','weightF')
        else:
            self.histogramOptions['weight'] = None

        optionNames = {
                    'treeVar': 'relPath',
                    'rebin': 'rebin',
                    'xAxis': 'xAxis',
                    'yAxis': 'yAxis',
                    'drawOption': 'drawOption',
                    'drawOptionData': 'drawOptionData',
                    'draw': 'draw',
                    'binList': 'binList',
                    'plotEqualSize': 'plotEqualSize',
                    'visualizeBlindCutThreshold': 'visualizeBlindCutThreshold',
                    'min': ['min', 'minX'],
                    'max': ['max', 'maxX'],
                    'blindCut': 'blindCut',
                    'minX': ['minX', 'min'],
                    'minY': ['minY', 'min'],
                    'minZ': ['minZ'],
                    'maxX': ['maxX', 'max'],
                    'maxY': ['maxY', 'max'],
                    'maxZ': ['maxZ'],
                    'nBins': ['nBins', 'nBinsX'],
                    'nBinsX': ['nBinsX', 'nBins'],
                    'nBinsY': ['nBinsY', 'nBins'],
                }
        numericOptions = ['rebin', 'min', 'minX', 'minY', 'maxX', 'maxY', 'nBins', 'nBinsX', 'nBinsY', 'minZ', 'maxZ']
        evalOptions = ['binList', 'plotEqualSize']
        for optionName, configKeys in optionNames.iteritems():
            # use the first available option from the config, first look in region definition, afterwards in plot definition
            configKeysList = configKeys if type(configKeys) == list else [configKeys]
            for configKey in configKeysList:
                if self.config.has_option(self.configSection, configKey):
                    self.histogramOptions[optionName] = self.config.get(self.configSection, configKey)
                    break
                elif self.config.has_option('plotDef:%s'%var, configKey):
                    self.histogramOptions[optionName] = self.config.get('plotDef:%s'%var, configKey)
                    break
            # convert numeric options to float/int
            if optionName in numericOptions and optionName in self.histogramOptions and type(self.histogramOptions[optionName]) == str:
                self.histogramOptions[optionName] = float(self.histogramOptions[optionName]) if ('.' in self.histogramOptions[optionName] or 'e' in self.histogramOptions[optionName]) else int(self.histogramOptions[optionName])
        
        # evaluate options given as python code
        for evalOption in evalOptions: 
            if evalOption in self.histogramOptions and type(evalOption) == str:
                self.histogramOptions[evalOption] = eval(self.histogramOptions[evalOption])

        # region/variable specific blinding cut
        if self.config.has_option(self.configSection, 'blindCuts'):
            blindCuts = eval(self.config.get(self.configSection, 'blindCuts'))
            if self.var in blindCuts:
                self.histogramOptions['blindCut'] = blindCuts[self.var]
                if '{var}' in self.histogramOptions['blindCut']:
                    self.histogramOptions['blindCut'] = self.histogramOptions['blindCut'].format(var=self.histogramOptions['treeVar'])
                print("\x1b[31mINFO: for region {region} var {var} using the blinding cut: {cut}\x1b[0m".format(region=self.region, var=self.var, cut=self.histogramOptions['blindCut']))

        self.groups = {}
        self.histograms = []
        self.legends = {}
        self.plotTexts = {}
        self.collectedObjects = []
        self.dataTitle = 'Data'
        self.maxRatioUncert = 0.5
        self.lumi = self.config.get('General','lumi')
        self.ratioError = None
        self.ratioPlot = None
        if SignalRegion:
            self.maxRatioUncert = 1000.
        self.outputTeX = False
        self.outputFileTemplate = "{outputFolder}/{prefix}.{ext}"
        try:
            self.outputFileFormats = [x.strip() for x in config.get('Plot_general','outputFormats').split(',') if len(x.strip())>0] 
        except:
            self.outputFileFormats = ["png"]
        
        if 'tex' in self.outputFileFormats:
            self.outputFileFormats = [x for x in self.outputFileFormats if x != 'tex']
            self.outputTeX = True

        self.plotTextMarginLeft = 0.16

        if self.debug:
            print ("INFO: StackMaker initialized!", self.histogramOptions['treeVar'], " min=", self.histogramOptions['minX'], " max=", self.histogramOptions['maxX'], "nBins=", self.histogramOptions['nBins'])

    def setPlotText(self, text):
        if type(text) == list:
            self.additionalTextLines = text
        elif type(text) == str:
            self.additionalTextLines = [text]
        else:
            print("ERROR: can't set plto text, unknown type:", type(text))

    # ------------------------------------------------------------------------------
    # draw text
    # ------------------------------------------------------------------------------
    @staticmethod
    def myText(txt="CMS Preliminary", ndcX=0.0, ndcY=0.0, size=0.8, color=None):
        ROOT.gPad.Update()
        text = ROOT.TLatex()
        text.SetNDC()
        if color:
            text.SetTextColor(color)
        text.SetTextSize(text.GetTextSize()*size)
        text.DrawLatex(ndcX,ndcY,txt)
        return text

    # ------------------------------------------------------------------------------
    # create histogram out of a tree
    # ------------------------------------------------------------------------------
    def addSampleTree(self, sample, sampleTree, groupName, cut='1'):
        print ("INFO: var=", self.var, "-> treeVar=\x1b[34m", self.histogramOptions['treeVar'] , "\x1b[0m add sample \x1b[34m", sample,"\x1b[0m from sampleTree \x1b[34m", sampleTree, "\x1b[0m to group \x1b[34m", groupName, "\x1b[0m")
        histogramOptions = self.histogramOptions.copy()
        histogramOptions['group'] = groupName

        histoMaker = HistoMaker(self.config, sample=sample, sampleTree=sampleTree, histogramOptions=histogramOptions) 
        sampleHistogram = histoMaker.getHistogram(cut)
        self.histograms.append({
            'name': sample.name,
            'histogram': sampleHistogram,
            'group': groupName
            })
    
    # add object to collection
    def addObject(self, object):
        self.collectedObjects.append(object)

    # ------------------------------------------------------------------------------
    # create canvas and load default style 
    # ------------------------------------------------------------------------------
    def initializeSplitCanvas(self):
        TdrStyles.tdrStyle()

        # initialize canvas
        self.canvas = ROOT.TCanvas(self.var, '', 600, 600)
        self.canvas.SetFillStyle(4000)
        self.canvas.SetFrameFillStyle(1000)
        self.canvas.SetFrameFillColor(0)
        self.canvas.SetTopMargin(0.035)
        self.canvas.SetBottomMargin(0.12)
       
        self.pads = {}
        self.pads['oben'] = ROOT.TPad('oben', 'oben', 0, 0.3, 1.0, 1.0)
        self.pads['oben'].SetBottomMargin(0)
        self.pads['oben'].SetFillStyle(4000)
        self.pads['oben'].SetFrameFillStyle(1000)
        self.pads['oben'].SetFrameFillColor(0)
        self.pads['unten'] = ROOT.TPad('unten', 'unten', 0, 0.0, 1.0, 0.3)
        self.pads['unten'].SetTopMargin(0.)
        self.pads['unten'].SetBottomMargin(0.35)
        self.pads['unten'].SetFillStyle(4000)
        self.pads['unten'].SetFrameFillStyle(1000)
        self.pads['unten'].SetFrameFillColor(0)

        self.pads['oben'].Draw()
        self.pads['unten'].Draw()

        self.pads['oben'].cd()
        return self.canvas

    # ------------------------------------------------------------------------------
    # create canvas and load default style 
    # ------------------------------------------------------------------------------
    def initializeCanvas(self):
        TdrStyles.tdrStyle()

        self.canvas = ROOT.TCanvas(self.var+'Comp','',600,600)
        self.canvas.SetFillStyle(4000)
        self.canvas.SetFrameFillStyle(1000)
        self.canvas.SetFrameFillColor(0)
        self.pads = {}
        if self.is2D:
            ROOT.gPad.SetTopMargin(0.05)
            ROOT.gPad.SetBottomMargin(0.13)
            ROOT.gPad.SetLeftMargin(0.17)
            ROOT.gPad.SetRightMargin(0.16)
        return self.canvas

    # ------------------------------------------------------------------------------
    # data/MC ratio
    # ------------------------------------------------------------------------------
    def drawRatioPlot(self, dataHistogram, mcHistogram):

        self.pads['unten'].cd()
        ROOT.gPad.SetTicks(1,1)

        self.legends['ratio'] = ROOT.TLegend(0.39, 0.85, 0.93, 0.97)
        self.legends['ratio'].SetLineWidth(2)
        self.legends['ratio'].SetBorderSize(0)
        self.legends['ratio'].SetFillColor(0)
        self.legends['ratio'].SetFillStyle(4000)
        self.legends['ratio'].SetTextSize(0.075)
        self.legends['ratio'].SetNColumns(2)

        # convert TGraphAsymmErrors to TH1D
        if type(dataHistogram) == ROOT.TGraphAsymmErrors:
            print("INFO: converting TGraphAsymmErrors to TH1D for ratio plot...")
            convertedDataHistogram = ROOT.TH1D("data_th1d","data_th1d",self.histogramOptions['nBins'],self.histogramOptions['minX'], self.histogramOptions['maxX'])
            pointX = array.array('d', [0.0, 0.0])
            pointY = array.array('d', [0.0, 0.0])
            for i in range(dataHistogram.GetN()):
                dataHistogram.GetPoint(i, pointX, pointY)
                convertedDataHistogram.SetBinContent(1+i, pointY[0])
                convertedDataHistogram.SetBinError(1+i, 0.5*(dataHistogram.GetErrorYhigh(i)+dataHistogram.GetErrorYlow(i)))
                convertedDataHistogram.SetDrawOption("EP")
            dataHistogram = convertedDataHistogram

        # draw ratio plot
        self.ratioPlot, error = getRatio(dataHistogram, mcHistogram, self.histogramOptions['minX'], self.histogramOptions['maxX'], "", self.maxRatioUncert, True)

        ksScore = dataHistogram.KolmogorovTest(mcHistogram)
        chiScore = dataHistogram.Chi2Test(mcHistogram, "UWCHI2/NDF")
        print ("INFO: data/MC ratio, KS test:", ksScore, " chi2:", chiScore)
        try:
            self.ratioPlot.SetStats(0)
            self.ratioPlot.GetXaxis().SetTitle(self.xAxis)
            self.ratioError = ROOT.TGraphErrors(error)
            self.ratioError.SetFillColor(ROOT.kGray+3)
            self.ratioError.SetFillStyle(3013)
            self.ratioPlot.Draw("E1")
            self.ratioError.Draw('SAME2')
        except Exception as e:
            print ("\x1b[31mERROR: with ratio histogram!", e, "\x1b[0m")

        # blinded region
        if 'blindCut' in self.histogramOptions:

            # check if the blinding cut has the simple form var<num
            isSimpleCut = False
            print("DEBUG:", self.histogramOptions['blindCut'], self.histogramOptions['treeVar'], self.histogramOptions['blindCut'].startswith(self.histogramOptions['treeVar']))
            if self.histogramOptions['blindCut'].startswith(self.histogramOptions['treeVar']):
                if 'visualizeBlindCutThreshold' in self.histogramOptions:
                    isSimpleCut = True
                    blindingCutThreshold = float(self.histogramOptions['visualizeBlindCutThreshold'])
                else:
                    cond = self.histogramOptions['blindCut'].split(self.histogramOptions['treeVar'])[1]
                    print("DEBUG: cond=", cond)
                    if cond.startswith('<'):
                        num = cond.replace('<=','').replace('<','')
                        print("DEBUG: num=",num)
                        try:
                            blindingCutThreshold = float(num)
                            isSimpleCut = True
                        except:
                            pass

            if isSimpleCut:
                if blindingCutThreshold >= self.ratioPlot.GetXaxis().GetXmin() and blindingCutThreshold<=self.ratioPlot.GetXaxis().GetXmax():

                    # get list of bin boundaries of ratio histogram, those might be different from the ones from the main histogram and are provided by the external ratio.C code.
                    bin_list = array.array('d', [0.0]*(self.ratioPlot.GetXaxis().GetNbins() + 1))
                    for i in range(self.ratioPlot.GetXaxis().GetNbins()):
                        bin_list[i] = self.ratioPlot.GetXaxis().GetBinLowEdge(1+i)
                    bin_list[self.ratioPlot.GetXaxis().GetNbins()] = self.ratioPlot.GetXaxis().GetXmax()

                    # make histogram to visualize blind cut with same bins as the ratio plot
                    blindedRegion = ROOT.TH1D("blind", "blind", self.ratioPlot.GetXaxis().GetNbins(), bin_list)
                    for i in range(self.ratioPlot.GetXaxis().GetNbins()):
                        binLowEdgeValue = self.ratioPlot.GetXaxis().GetBinLowEdge(1+i)
                        value = 1.1
                        if binLowEdgeValue >= blindingCutThreshold:
                            # shaded area
                            error = 0.6
                        else:
                            error = 0.0
                        blindedRegion.SetBinContent(1+i, value)
                        blindedRegion.SetBinError(1+i, error)
                    blindedRegion.SetFillColor(ROOT.kRed)
                    blindedRegion.SetFillStyle(3018)
                    blindedRegion.SetMarkerSize(0)
                    blindedRegion.Draw("SAME E2")
                    self.addObject(blindedRegion)

        self.m_one_line = ROOT.TLine(self.histogramOptions['minX'], 1, self.histogramOptions['maxX'], 1)
        self.m_one_line.SetLineStyle(ROOT.kSolid)
        self.m_one_line.Draw("Same")

        self.legends['ratio'].AddEntry(self.ratioError, self.mcUncertaintyLegend,"f")
        self.legends['ratio'].Draw() 
        if not self.blind:
            self.addObject(self.myText("#chi^{2}_{ }#lower[0.1]{/^{}#it{dof} = %.2f}"%(chiScore), self.plotTextMarginLeft, 0.895, 1.55))
            t0 = ROOT.TText()
            t0.SetTextSize(ROOT.gStyle.GetLabelSize()*2.4)
            t0.SetTextFont(ROOT.gStyle.GetLabelFont())
            if not self.log:
                t0.DrawTextNDC(0.1059, 0.96, "0")

    def drawSampleLegend(self, groupedHistograms, theErrorGraph):
        if 'oben' in self.pads and self.pads['oben']:
            self.pads['oben'].cd()
        self.legends['left'] = ROOT.TLegend(0.45, 0.6,0.75,0.92)
        self.legends['left'].SetLineWidth(2)
        self.legends['left'].SetBorderSize(0)
        self.legends['left'].SetFillColor(0)
        self.legends['left'].SetFillStyle(4000)
        self.legends['left'].SetTextFont(62)
        self.legends['left'].SetTextSize(0.035)
        self.legends['right'] = ROOT.TLegend(0.68, 0.6,0.92,0.92)
        self.legends['right'].SetLineWidth(2)
        self.legends['right'].SetBorderSize(0)
        self.legends['right'].SetFillColor(0)
        self.legends['right'].SetFillStyle(4000)
        self.legends['right'].SetTextFont(62)
        self.legends['right'].SetTextSize(0.035)
 
        if self.dataGroupName in groupedHistograms:
            self.legends['left'].AddEntry(groupedHistograms[self.dataGroupName], self.dataTitle, 'P')
        groupNames = list(set([groupName for groupName, groupHistogram in groupedHistograms.iteritems()]))
        groupNamesOrdered = self.setup + sorted([x for x in groupNames if x not in self.setup])

        numLegendEntries = len(groupNames) + 2
        for itemPosition, groupName in enumerate(groupNamesOrdered): 
            if groupName != self.dataGroupName and groupName in groupedHistograms:
                legendEntryName = self.typLegendDict[groupName] if groupName in self.typLegendDict else groupName
                if itemPosition < numLegendEntries/2.-2:
                    self.legends['left'].AddEntry(groupedHistograms[groupName], legendEntryName, 'F')
                else:
                    self.legends['right'].AddEntry(groupedHistograms[groupName], legendEntryName, 'F')
            elif groupName not in groupedHistograms:
                print("WARNING: histogram group not found:", groupName)
        if theErrorGraph: 
            self.legends['right'].AddEntry(theErrorGraph, self.mcUncertaintyLegend, "fl")
        self.canvas.Update()
        ROOT.gPad.SetTicks(1,1)
        self.legends['left'].SetFillColor(0)
        self.legends['left'].SetBorderSize(0)
        self.legends['right'].SetFillColor(0)
        self.legends['right'].SetBorderSize(0)
        self.legends['left'].Draw()
        self.legends['right'].Draw()

    def drawPlotTexts(self):
        if 'oben' in self.pads and self.pads['oben']:
            self.pads['oben'].cd()
        posY = 0.88
        if type(self.plotTitle) == list:
            size = 1.04
            for plotTitleLine in self.plotTitle:
                self.addObject(self.myText(plotTitleLine, self.plotTextMarginLeft + (0.03 if self.is2D else 0),posY,size))
                posY -= 0.05
                size *= 0.77
        else:
            self.addObject(self.myText(self.plotTitle,self.plotTextMarginLeft+(0.03 if self.is2D else 0),posY,1.04))
            posY -= 0.05
        print ('self.lumi is', self.lumi)
        try:
            self.addObject(self.myText("#sqrt{s} = %s, L = %.2f fb^{-1}"%(self.anaTag, (float(self.lumi)/1000.0)), self.plotTextMarginLeft+(0.03 if self.is2D else 0), posY, 0.75))
        except Exception as e:
            print ("WARNING: exception while adding text: ", e)
            pass
        dataNames = list(set([histogram['name'] for histogram in self.histograms if histogram['group'] == self.dataGroupName]))
        addFlag = None
        addFlag2 = None
        isZee = False
        isZmm = False
        for data_ in dataNames:
            if 'DoubleEG' in data_:
                isZee = True
            if 'DoubleMuon' in data_:
                isZmm = True
        if ('Zee' in dataNames and 'Zmm' in dataNames) or (isZee and isZmm):
            addFlag = 'Z(l^{-}l^{+})H(b#bar{b})'
        elif 'Zee' in dataNames or isZee:
            addFlag = 'Z(e^{-}e^{+})H(b#bar{b})'
        elif 'Zmm' in dataNames or isZmm:
            addFlag = 'Z(#mu^{-}#mu^{+})H(b#bar{b})'
        elif 'Znn' in dataNames:
            addFlag = 'Z(#nu#nu)H(b#bar{b})'
        elif 'Wmn' in dataNames:
            addFlag = 'W(#mu#nu)H(b#bar{b})'
        elif 'Wen' in dataNames:
            addFlag = 'W(e#nu)H(b#bar{b})'
        #self.addObject(self.myText(addFlag, self.plotTextMarginLeft+(0.03 if self.is2D else 0), 0.78))
        #print('self.region is', self.region)
        #import sys
        #sys.exit()

        if self.region == 'Whf_BOOSTv2':
            addFlag = 'W(l#nu)H(b#bar{b})'
            addFlag2 = 'Boosted Analysis'
        elif self.region == 'tt_BOOST':
            addFlag = 'W(l#nu)H(b#bar{b})'
            addFlag2 = 'Boosted Analysis'
        elif self.region == 'Wlf_BOOSTv11':
            addFlag = 'W(l#nu)H(b#bar{b})'
            addFlag2 = 'Boosted Analysis'
        elif self.region == 'Whf_BOOSTv2_e':
            addFlag = 'W(e#nu)H(b#bar{b})'
            addFlag2 = 'Boosted Analysis'
        elif self.region == 'tt_BOOST_e':
            addFlag = 'W(e#nu)H(b#bar{b})'
            addFlag2 = 'Boosted Analysis'
        elif self.region == 'Wlf_BOOSTv11_e':
            addFlag = 'W(e#nu)H(b#bar{b})'
            addFlag2 = 'Boosted Analysis'
        elif self.region == 'Whf_BOOSTv2_m':
            addFlag = 'W(#mu#nu)H(b#bar{b})'
            addFlag2 = 'Boosted Analysis'
        elif self.region == 'tt_BOOST_m':
            addFlag = 'W(#mu#nu)H(b#bar{b})'
            addFlag2 = 'Boosted Analysis'
        elif self.region == 'Wlf_BOOSTv11_m':
            addFlag = 'W(#mu#nu)H(b#bar{b})'
            addFlag2 = 'Boosted Analysis'
          
        if addFlag2:
            if not addFlag in self.additionalTextLines:
                self.additionalTextLines.insert(0,addFlag)
        if addFlag:
            if not addFlag2 in self.additionalTextLines:
                self.additionalTextLines.insert(0,addFlag2)

        try:
            for labelName, label in self.plotLabels.iteritems():
                self.addObject(self.myText(label['text'], label['x'], label['y'], label['size']))
        except:
            pass

        try:
            for j, additionalTextLine in enumerate(self.additionalTextLines):
                #self.addObject(self.myText(additionalTextLine, self.plotTextMarginLeft, 0.73-0.03*j, 0.6))
                self.addObject(self.myText(additionalTextLine, self.plotTextMarginLeft, 0.79-0.04*j, 0.6))
        except Exception as e:
            print(e)

        #print 'Add Flag %s' %self.addFlag2
        #if self.addFlag2:
        #    tAddFlag2 = self.myText(self.addFlag2,0.17,0.73)

    # adds TH1 objects together
    @staticmethod
    def sumHistograms(histograms, outputName='summed_histogram'):
        summedHistogram = None
        for histogram in histograms:
            if summedHistogram:
                summedHistogram.Add(histogram)
            else:
                summedHistogram = histogram.Clone(outputName)
        return summedHistogram

    # ------------------------------------------------------------------------------
    # draw the stacked histograms 
    # ------------------------------------------------------------------------------
    def Draw(self, outputFolder='./', prefix='', normalize=False):

        self.is2D = any([isinstance(h['histogram'], ROOT.TH2) for h in self.histograms])

        dataGroupName = self.dataGroupName
        # group ("sum") MC+DATA histograms 
        groupedHistograms = {}
        histogramGroups = list(set([histogram['group'] for histogram in self.histograms]))
        for histogramGroup in histogramGroups:
            histogramsInGroup = [histogram['histogram'] for histogram in self.histograms if histogram['group'] == histogramGroup]
            groupedHistograms[histogramGroup] = NewStackMaker.sumHistograms(histograms=histogramsInGroup, outputName="group_" + histogramGroup)
            try:
                groupedHistograms[histogramGroup].SetStats(0)
            except:
                pass

        # MC histograms, defined in setup
        mcHistogramGroups = list(set([histogram['group'] for histogram in self.histograms if histogram['group']!=dataGroupName]))
        mcHistogramGroupsToPlot = sorted(mcHistogramGroups, key=lambda x: self.setup.index(x) if x in self.setup else 9999)
        mcHistogramGroupsUndefined = [x for x in mcHistogramGroups if x not in self.setup]
        if len(mcHistogramGroupsUndefined) > 0:
            print("\x1b[97m\x1b[41mWARNING: some MC samples are not defined in 'setup' definition for plots: \x1b[0m")
            for hiddenGroup in mcHistogramGroupsUndefined:
                print(" > ", hiddenGroup, " is not defined in setup")
        if dataGroupName in mcHistogramGroupsToPlot:
            raise Exception("DATA contained in MC groups!")

        c = self.initializeCanvas() if (normalize or self.is2D or dataGroupName not in histogramGroups) else self.initializeSplitCanvas()

        # add summed MC histograms to stack
        allStack = ROOT.THStack(self.var, '')
        colorDict = eval(self.config.get('Plot_general', 'colorDict'))
        maximumNormalized = 0
        for groupName in mcHistogramGroupsToPlot[::-1]:
            if groupName in groupedHistograms and groupName != dataGroupName:
                if groupName in colorDict:
                    if normalize:
                        groupedHistograms[groupName].SetFillColor(0)
                        groupedHistograms[groupName].SetLineColor(colorDict[groupName])
                        groupedHistograms[groupName].SetLineWidth(3)
                    else:
                        groupedHistograms[groupName].SetFillColor(colorDict[groupName])
                if groupedHistograms[groupName]:
                    groupedHistograms[groupName].SetStats(0)
                    if normalize and groupedHistograms[groupName].Integral()>0:
                        groupedHistograms[groupName].Scale(1./groupedHistograms[groupName].Integral())
                        if groupedHistograms[groupName].GetMaximum() > maximumNormalized:
                            maximumNormalized = groupedHistograms[groupName].GetMaximum()
                    allStack.Add(groupedHistograms[groupName])

        # draw options
        drawOption = "hist" if not normalize else "histnostack"
        if self.is2D:
            drawOption = self.histogramOptions['drawOption'] if 'drawOption' in self.histogramOptions else 'colz'

        # draw stack/sum
        if self.is2D:
            self.plotLabels['topright1'] = {'text': '2Dplot', 'x': 0.69, 'y': 0.9, 'size': 0.7}
            if 'draw' in self.histogramOptions and self.histogramOptions['draw'].strip() == self.dataGroupName:
                allStack = NewStackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.histograms if histogram['group'] == self.dataGroupName], outputName='summedDataHistograms')
                self.plotLabels['topright1']['text'] = 'DATA'
            elif 'draw' in self.histogramOptions and self.histogramOptions['draw'].strip().upper() == 'RATIO':
                allStackData = NewStackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.histograms if histogram['group'] == self.dataGroupName], outputName='summedDataHistograms')
                allStackMc = NewStackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.histograms if histogram['group'] in mcHistogramGroupsToPlot], outputName='summedMcHistograms')
                allStack = allStackData.Clone('summedRatioHistogram')
                allStack.Sumw2()
                allStack.Divide(allStackMc)
                self.plotLabels['topright1']['text'] = 'DATA/MC'
                try:
                    unityPos = 0.33
                    try:
                        if 'minZ' in self.histogramOptions and 'maxZ' in self.histogramOptions:
                            unityPos = (1.0-self.histogramOptions['minZ'])/(self.histogramOptions['maxZ']-self.histogramOptions['minZ'])
                    except:
                        pass
                    stops = array.array('d', [0.0, unityPos, 1.0])
                    reds = array.array('d', [0.34, 0.63, 1.0])
                    greens = array.array('d', [0.34, 0.63, 0])
                    blues = array.array('d', [0.63, 0.63, 0])
                    nc = 20
                    ROOT.TColor.CreateGradientColorTable(len(stops), stops, reds, greens, blues, nc)
                    ROOT.gStyle.SetNumberContours(nc)
                except Exception as e:
                    print("\x1b[31m",e,"\x1b[0m")
            else:
                allStack = NewStackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.histograms if histogram['group'] in mcHistogramGroupsToPlot], outputName='summedMcHistograms')
                self.plotLabels['topright1']['text'] = 'MC'
            allStack.SetStats(0)
            allStack.SetTitle('')
        ROOT.gPad.SetLogy(0)
        allStack.Draw(drawOption)

        # set axis titles
        if self.is2D:
            yTitle = self.yAxis
        else:
            try:
                if dataGroupName in groupedHistograms and not groupedHistograms[dataGroupName].GetSumOfWeights() % 1 == 0.0:
                    yTitle = 'S/(S+B) weighted entries'
                else:
                    yTitle = 'Entries'
                if '/' not in yTitle:
                    if allStack and allStack.GetXaxis():
                        if 'GeV' in self.xAxis:
                            yAppend = '%.0f' %(allStack.GetXaxis().GetBinWidth(1))
                        else:
                            yAppend = '%.2f' %(allStack.GetXaxis().GetBinWidth(1))
                        yTitle = '%s / %s' %(yTitle, yAppend)
                        if 'GeV' in self.xAxis:
                            yTitle += ' GeV'
            except:
                yTitle = "Entries"
        if allStack and allStack.GetXaxis():
            allStack.GetYaxis().SetTitle(yTitle if yTitle else '-')
            allStack.GetXaxis().SetRangeUser(self.histogramOptions['minX'], self.histogramOptions['maxX'])
            if not self.is2D:
                allStack.GetYaxis().SetRangeUser(0,20000)
        if not self.is2D:
            if normalize:
                Ymax = maximumNormalized * 1.5
            else:
                Ymax = max(allStack.GetMaximum(), groupedHistograms[dataGroupName].GetMaximum() if dataGroupName in groupedHistograms else 0) * 1.7
            if self.log and not normalize:
                allStack.SetMinimum(0.1)
                Ymax = Ymax*ROOT.TMath.Power(10,1.2*(ROOT.TMath.Log(1.2*(Ymax/0.2))/ROOT.TMath.Log(10)))*(0.2*0.1)
                ROOT.gPad.SetLogy()
            else:
                ROOT.gPad.SetLogy(0)
            allStack.SetMaximum(Ymax)
        if (not normalize and dataGroupName in groupedHistograms) and not self.is2D:
            allStack.GetXaxis().SetLabelOffset(999)
            allStack.GetXaxis().SetLabelSize(0)
        else:
            allStack.GetXaxis().SetTitle(self.xAxis)

        if self.is2D:
            if 'minZ' in self.histogramOptions and 'maxZ' in self.histogramOptions:
                allStack.GetZaxis().SetRangeUser(self.histogramOptions['minZ'], self.histogramOptions['maxZ'])

        # draw DATA
        if dataGroupName in groupedHistograms and not self.is2D:
            drawOption = self.histogramOptions['drawOptionData'] if 'drawOptionData' in self.histogramOptions else 'PE'
            if allStack and allStack.GetXaxis():
                drawOption += ',SAME'
            if normalize and groupedHistograms[dataGroupName].Integral() > 0:
                groupedHistograms[dataGroupName].Scale(1./groupedHistograms[dataGroupName].Integral())
            groupedHistograms[dataGroupName].Draw(drawOption)

        # draw total entry number
        if not self.is2D and 'drawOption' in self.histogramOptions and 'TEXT' in self.histogramOptions['drawOption'].upper():
            mcHistogram0 = NewStackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.histograms if histogram['group'] in mcHistogramGroupsToPlot], outputName='summedMcHistograms0')
            mcHistogram0.SetLineColor(ROOT.kBlack)
            mcHistogram0.SetMarkerColor(ROOT.kBlack)
            mcHistogram0.SetMarkerStyle(1)
            #mcHistogram0.SetMarkerSize(0.001)
            mcHistogram0.SetStats(0)
            mcHistogram0.Draw("SAME TEXT0")
            print("drawn total entry histogram!!!")
            binContents = ["%1.4f"%mcHistogram0.GetBinContent(1+j) for j in range(mcHistogram0.GetXaxis().GetNbins())]
            print("bin contents:", ", ".join(binContents))

        # draw ratio plot
        theErrorGraph = None
        mcHistogram   = None
        if not normalize and not self.is2D:
            if dataGroupName in groupedHistograms:
                dataHistogram = groupedHistograms[dataGroupName]
                mcHistogram = NewStackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.histograms if histogram['group'] in mcHistogramGroupsToPlot], outputName='summedMcHistograms')
                self.drawRatioPlot(dataHistogram, mcHistogram)

                self.pads['oben'].cd()
                theErrorGraph = ROOT.TGraphErrors(mcHistogram)
                theErrorGraph.SetFillColor(ROOT.kGray+3)
                theErrorGraph.SetFillStyle(3013)
                theErrorGraph.Draw('SAME2')
            else:
                print("INFO: no DATA available")

        # draw legend
        if not self.is2D:
            self.drawSampleLegend(groupedHistograms, theErrorGraph)

        # draw various labels
        if not normalize:
            self.drawPlotTexts()

        # save to file
        for ext in self.outputFileFormats:
            outputFileName = self.outputFileTemplate.format(outputFolder=outputFolder, prefix=prefix, prefixSeparator='_' if len(prefix)>0 else '', var=self.var, ext=ext)
            c.SaveAs(outputFileName)
            if os.path.isfile(outputFileName):
                print("INFO: saved as \x1b[34m", outputFileName, "\x1b[0m")
            else:
                print("\x1b[31mERROR: could not save canvas to the file:", outputFileName, "\x1b[0m")
        if self.outputTeX:
            outputFileName = self.outputFileTemplate.format(outputFolder=outputFolder, prefix=prefix, prefixSeparator='_' if len(prefix)>0 else '', var=self.var, ext='tex')
            #ROOT.gPad.Print(outputFileName)
            c.SaveAs(outputFileName)
            print("INFO: saved as \x1b[32mTeX \x1b[34m", outputFileName, "\x1b[0m")

        self.histoCounts = {'unweighted':{}, 'weighted': {}}

        # save shapes
        if not normalize and self.saveShapes:
            mcHistogram = NewStackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.histograms if histogram['group'] in mcHistogramGroupsToPlot], outputName='summedMcHistograms')
            print("MC:", mcHistogram)
            try:
                outputFileName = self.outputFileTemplate.format(outputFolder=outputFolder, prefix=prefix, prefixSeparator='_' if len(prefix)>0 else '', var=self.var,  ext="shapes.root")
                shapesFile = ROOT.TFile.Open(outputFileName, "RECREATE")
                if dataGroupName and dataGroupName in groupedHistograms:
                    groupedHistograms[dataGroupName].SetDirectory(shapesFile)
                mcHistogram.SetDirectory(shapesFile)
                for histogram in self.histograms:
                    histogram['histogram'].SetDirectory(shapesFile)

                try:
                    signals = self.config.get('Plot_general','allSIG') 
                    backgroundHistogram = NewStackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.histograms if histogram['group'] in mcHistogramGroupsToPlot and histogram['name'] not in signals], outputName='summedBackgroundHistograms')
                    signalHistogram = NewStackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.histograms if histogram['group'] in mcHistogramGroupsToPlot and histogram['name'] in signals], outputName='summedSignalHistograms')
                    backgroundHistogram.SetDirectory(shapesFile)
                    signalHistogram.SetDirectory(shapesFile)
                    
                    sspb_sum = 0.0
                    q_a_sum = 0.0
                    s_sum = 0.0
                    b_sum = 0.0
                    for i in range(backgroundHistogram.GetXaxis().GetNbins()):
                        s = signalHistogram.GetBinContent(1+i)
                        b = backgroundHistogram.GetBinContent(1+i)
                        sspb = s/math.sqrt(s+b) if s+b > 0 else 0
                        sspb_sum += sspb*sspb
                        q_a = math.sqrt(2*((s+b)*math.log(1+s/b)-s)) if b>0 else 0
                        q_a_sum += q_a*q_a
                        s_sum += s
                        b_sum += b
                        print("{s: <12.3f}{b: <12.3f}{a: <12.3f}{q: <12.3f}".format(s=s, b=b, a=sspb, q=q_a))
                    print("-"*48)
                    q_a_sum = math.sqrt(q_a_sum)
                    sspb_sum = math.sqrt(sspb_sum)
                    print("{s: <12.3f}{b: <12.3f}{a: <12.3f}{q: <12.3f}".format(s=s_sum, b=b_sum, a=sspb_sum, q=q_a_sum))

                except Exception as e:
                    print("EXCEPTION:", e)
                shapesFile.Write()
            except Exception as e:
                print("ERROR: could not save shapes:", e)

        # print yield tables
        try:
            for histogram in self.histograms:
                self.histoCounts['weighted'][histogram['name']] = histogram['histogram'].Integral()
                self.histoCounts['unweighted'][histogram['name']] = histogram['histogram'].GetEntries()

            # print n events and weights for each sample
            keys = list(set(sorted([histogram['name'] for histogram in self.histograms])))
            for key in keys:
                print(key.ljust(50),("%d"%self.histoCounts['unweighted'][key]).ljust(10), ("%f"%self.histoCounts['weighted'][key]).ljust(10))

            ## print n events and weights for group
            self.groupCounts =  {'unweighted':{}, 'weighted': {}}
            for histogram in self.histograms:
                group_ = histogram['group']
                if not group_ in self.groupCounts['weighted']:
                    self.groupCounts['weighted'][group_] = histogram['histogram'].Integral()
                    self.groupCounts['unweighted'][group_] = histogram['histogram'].GetEntries()
                else:
                    self.groupCounts['weighted'][group_] += histogram['histogram'].Integral()
                    self.groupCounts['unweighted'][group_] += histogram['histogram'].GetEntries()

            print('--------------------')
            print('Printing the #events and yield by group')
            print('--------------------\n')

            #print('self.groupCounts[weighted] is',self.groupCounts['weighted'])
            keys = list(set(sorted([histogram['group'] for histogram in self.histograms])))
            for key in keys:
                #print('groupName is', key)
                print(key.ljust(50),("%d"%self.groupCounts['unweighted'][key]).ljust(10), ("%f"%self.groupCounts['weighted'][key]).ljust(10))

	    sum = 0
            for key in keys:
                sum = self.groupCounts['weighted'][key] + sum

            print('total weighted events are:', sum)
        except Exception as e:
            print("ERROR: could not obtain counts (not implemented for TGraphAsymErrors yet)", e)

        # save data histogram
        if self.config.has_option('Plot_general','saveDataHistograms') and eval(self.config.get('Plot_general','saveDataHistograms')):
            if dataGroupName in groupedHistograms:
                outputFileName = self.outputFileTemplate.format(outputFolder=outputFolder, prefix='DATA_'+prefix, prefixSeparator='_' if len(prefix)>0 else '', var=self.var, ext="root")
                dataOutputFile = ROOT.TFile.Open(outputFileName, "recreate")
                groupedHistograms[dataGroupName].SetDirectory(dataOutputFile)
                dataOutputFile.Write()
                dataOutputFile.Close()
