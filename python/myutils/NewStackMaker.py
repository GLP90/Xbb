from __future__ import print_function
import ROOT 
ROOT.gROOT.SetBatch(True)
import TdrStyles
import os

from Ratio import getRatio
from NewHistoMaker import NewHistoMaker as HistoMaker
from sampleTree import SampleTree as SampleTree

#------------------------------------------------------------------------------
# produces histograms from trees with HistoMaker, groups them, and draws a
# stacked histogram
#------------------------------------------------------------------------------
class NewStackMaker:
    def __init__(self, config, var, region, SignalRegion, setup=None, subcut = ''):
        self.config = config
        self.var = var
        self.region = region
        self.configSection = 'Plot:%s'%region
        self.dataGroupName = 'DATA'
        self.anaTag = self.config.get("Analysis", "tag")
        self.subcut = subcut
        self.forceLog = None
        self.normalize = eval(self.config.get(self.configSection, 'Normalize'))
        self.log = eval(self.config.get(self.configSection, 'log'))
        self.AddErrors = False
        if self.config.has_option('plotDef:%s'%var, 'log') and not self.log:
            self.log = eval(self.config.get('plotDef:%s'%var,'log'))
        self.blind = eval(self.config.get(self.configSection,'blind'))
        self.xAxis = self.config.get('plotDef:%s'%self.var,'xAxis')
        self.typLegendDict = eval(config.get('Plot_general','typLegendDict'))
        if setup is None:
            self.setup = [x.strip() for x in self.config.get('Plot_general', 'setupLog' if self.log else 'setup').split(',') if len(x.strip()) > 0]
        else:
            self.setup = setup

        # TODO: move to config file
        if not SignalRegion: 
            if 'ZH' in self.setup:
                self.setup.remove('ZH')
            if 'WH' in self.setup:
                self.setup.remove('WH')
                self.setup.remove('ggZH')
        self.rebin = 1
        self.histogramOptions = {
                'rebin': 1,
                'var': self.var,
                }
        if self.config.has_option(self.configSection,'rebin'):
            self.histogramOptions['rebin'] = eval(self.config.get(self.configSection,'rebin'))
        if self.config.has_option(self.configSection,'nBins'):
            self.histogramOptions['nBins'] = int(eval(self.config.get(self.configSection,'nBins'))/self.histogramOptions['rebin'])
        else:
            self.histogramOptions['nBins'] = int(eval(self.config.get('plotDef:%s'%var,'nBins'))/self.histogramOptions['rebin'])
        if self.config.has_option(self.configSection,'min'):
            self.histogramOptions['xMin'] = eval(self.config.get(self.configSection,'min'))
        else:
            self.histogramOptions['xMin'] = eval(self.config.get('plotDef:%s'%var,'min'))
        if self.config.has_option(self.configSection,'max'):
            self.histogramOptions['xMax'] = eval(self.config.get(self.configSection,'max'))
        else:
            self.histogramOptions['xMax'] = eval(self.config.get('plotDef:%s'%var,'max'))
        self.histogramOptions['treeVar'] = self.config.get('plotDef:%s'%var,'relPath')

        if self.config.has_option('Weights','weightF'):
            self.histogramOptions['weight'] = self.config.get('Weights','weightF')
        else:
            self.histogramOptions['weight'] = None

        self.groups = {}
        self.histograms = []
        self.legends = {}
        self.plotTexts = {}
        self.collectedObjects = []
        self.dataTitle = 'Data'
        self.maxRatioUncert = 0.5
        self.lumi = self.config.get('Plot_general','lumi')
        self.ratioError = None
        self.ratioPlot = None
        if SignalRegion:
            self.maxRatioUncert = 1000.
        #self.outputFileTemplate = "{outputFolder}/{prefix}{prefixSeparator}plot_{var}.{ext}"
        self.outputFileTemplate = "{outputFolder}/{prefix}.{ext}"
        try:
            self.outputFileFormats = [x.strip() for x in config.get('Plot_general','outputFormats').split(',') if len(x.strip())>0] 
        except:
            self.outputFileFormats = ["png"]

        print ("INFO: StackMaker initialized!", self.histogramOptions['treeVar'], " min=", self.histogramOptions['xMin'], " max=", self.histogramOptions['xMax'], "nBins=", self.histogramOptions['nBins'])

    #------------------------------------------------------------------------------
    # draw text
    #------------------------------------------------------------------------------
    @staticmethod
    def myText(txt="CMS Preliminary", ndcX=0.0, ndcY=0.0, size=0.8):
        ROOT.gPad.Update()
        text = ROOT.TLatex()
        text.SetNDC()
        text.SetTextColor(ROOT.kBlack)
        text.SetTextSize(text.GetTextSize()*size)
        text.DrawLatex(ndcX,ndcY,txt)
        return text

    #------------------------------------------------------------------------------
    # create histogram out of a tree
    #------------------------------------------------------------------------------
    def addSampleTree(self, sample, sampleTree, groupName):
        print ("INFO: var=", self.var, "-> treeVar=\x1b[34m", self.histogramOptions['treeVar'] , "\x1b[0m add sample \x1b[34m", sample,"\x1b[0m from sampleTree \x1b[34m", sampleTree, "\x1b[0m to group \x1b[34m", groupName, "\x1b[0m")
        histogramOptions = self.histogramOptions.copy()
        histogramOptions['group'] = groupName
        histoMaker = HistoMaker(self.config, sample=sample, sampleTree=sampleTree, histogramOptions=histogramOptions) 
        sampleHistogram = histoMaker.getHistogram()
        self.histograms.append({
            'name': sample.name,
            'histogram': sampleHistogram,
            'group': groupName
            })
    
    # add object to collection
    def addObject(self, object):
        self.collectedObjects.append(object)

    #------------------------------------------------------------------------------
    # create canvas and load default style 
    #------------------------------------------------------------------------------
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

    #------------------------------------------------------------------------------
    # create canvas and load default style 
    #------------------------------------------------------------------------------
    def initializeCanvas(self):
        TdrStyles.tdrStyle()

        self.canvas = ROOT.TCanvas(self.var+'Comp','',600,600)
        self.canvas.SetFillStyle(4000)
        self.canvas.SetFrameFillStyle(1000)
        self.canvas.SetFrameFillColor(0)
        return self.canvas
    #------------------------------------------------------------------------------
    #  
    #------------------------------------------------------------------------------
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

        # draw ratio plot
        self.ratioPlot, error = getRatio(dataHistogram, mcHistogram, self.histogramOptions['xMin'], self.histogramOptions['xMax'], "", self.maxRatioUncert, True)
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

        self.m_one_line = ROOT.TLine(self.histogramOptions['xMin'], 1, self.histogramOptions['xMax'], 1)
        self.m_one_line.SetLineStyle(ROOT.kSolid)
        self.m_one_line.Draw("Same")

        if not self.AddErrors:
            self.legends['ratio'].AddEntry(self.ratioError,"MC uncert. (stat.)","f")
        else:
            self.legends['ratio'].AddEntry(self.ratioError,"MC uncert. (stat. + syst.)","f")
        self.legends['ratio'].Draw() 
        if not self.blind:
            self.addObject(self.myText("#chi^{2}_{ }#lower[0.1]{/^{}#it{dof} = %.2f}"%(chiScore), 0.17, 0.895, 1.55))
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
            if groupName != self.dataGroupName:
                legendEntryName = self.typLegendDict[groupName] if groupName in self.typLegendDict else groupName
                if itemPosition < numLegendEntries/2.-2:
                    self.legends['left'].AddEntry(groupedHistograms[groupName], legendEntryName, 'F')
                else:
                    self.legends['right'].AddEntry(groupedHistograms[groupName], legendEntryName, 'F')
        if theErrorGraph: 
            if not self.AddErrors:
                self.legends['right'].AddEntry(theErrorGraph, "MC uncert. (stat.)", "fl")
            else:
                self.legends['right'].AddEntry(theErrorGraph, "MC uncert. (stat.+ syst.)", "fl")
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
        self.addObject(self.myText("CMS",0.17,0.88,1.04))
        print ('self.lumi is', self.lumi)
        try:
            self.addObject(self.myText("#sqrt{s} =  %s, L = %.2f fb^{-1}"%(self.anaTag, (float(self.lumi)/1000.0)), 0.17, 0.83))
        except Exception as e:
            print ("WARNING: exception while adding text: ", e)
            pass
        dataNames = list(set([histogram['name'] for histogram in self.histograms if histogram['group'] == self.dataGroupName]))
        addFlag = ''
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
        self.addObject(self.myText(addFlag, 0.17, 0.78))
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

    #------------------------------------------------------------------------------
    # draw the stacked histograms 
    #------------------------------------------------------------------------------
    def Draw(self, outputFolder='./', prefix='', normalize=False):
        c = self.initializeCanvas() if normalize else self.initializeSplitCanvas()

        dataGroupName = self.dataGroupName
        # group ("sum") MC+DATA histograms 
        groupedHistograms = {}
        histogramGroups = list(set([histogram['group'] for histogram in self.histograms]))
        for histogramGroup in histogramGroups:
            histogramsInGroup = [histogram['histogram'] for histogram in self.histograms if histogram['group'] == histogramGroup]
            groupedHistograms[histogramGroup] = NewStackMaker.sumHistograms(histograms=histogramsInGroup, outputName="group_" + histogramGroup)

        # add summed MC histograms to stack
        allStack = ROOT.THStack(self.var, '')
        colorDict = eval(self.config.get('Plot_general', 'colorDict'))
        maximumNormalized = 0
        for groupName in self.setup[::-1]:
            if groupName in groupedHistograms and groupName != dataGroupName:
                if groupName in colorDict:
                    if normalize:
                        groupedHistograms[groupName].SetFillColor(0)
                        groupedHistograms[groupName].SetLineColor(colorDict[groupName])
                        groupedHistograms[groupName].SetLineWidth(3)
                    else:
                        groupedHistograms[groupName].SetFillColor(colorDict[groupName])
                if groupedHistograms[groupName]:
                    if normalize and groupedHistograms[groupName].Integral()>0:
                        groupedHistograms[groupName].Scale(1./groupedHistograms[groupName].Integral())
                        if groupedHistograms[groupName].GetMaximum() > maximumNormalized:
                            maximumNormalized = groupedHistograms[groupName].GetMaximum()
                    allStack.Add(groupedHistograms[groupName])

        # draw stack
        allStack.Draw("hist" if not normalize else "histnostack")
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
        if allStack and allStack.GetXaxis():
            allStack.GetYaxis().SetTitle(yTitle)
            allStack.GetXaxis().SetRangeUser(self.histogramOptions['xMin'], self.histogramOptions['xMax'])
            allStack.GetYaxis().SetRangeUser(0,20000)
        if normalize:
            Ymax = maximumNormalized * 1.5
        else:
            Ymax = max(allStack.GetMaximum(), groupedHistograms[dataGroupName].GetMaximum() if dataGroupName in groupedHistograms else 0) * 1.7
        if self.log and not self.normalize:
            allStack.SetMinimum(0.1)
            Ymax = Ymax*ROOT.TMath.Power(10,1.2*(ROOT.TMath.Log(1.2*(Ymax/0.2))/ROOT.TMath.Log(10)))*(0.2*0.1)
            ROOT.gPad.SetLogy()
        else:
            ROOT.gPad.SetLogy(0)
        allStack.SetMaximum(Ymax)
        if not normalize:
            allStack.GetXaxis().SetLabelOffset(999)
            allStack.GetXaxis().SetLabelSize(0)
        else:
            allStack.GetXaxis().SetTitle(self.xAxis)

        # draw DATA
        if dataGroupName in groupedHistograms:
            drawOption = 'PE'
            if allStack and allStack.GetXaxis():
                drawOption += ',SAME'
            if normalize and groupedHistograms[dataGroupName].Integral() > 0:
                groupedHistograms[dataGroupName].Scale(1./groupedHistograms[dataGroupName].Integral())
            groupedHistograms[dataGroupName].Draw(drawOption)

        # draw ratio plot
        if not normalize:
            dataHistogram = groupedHistograms[dataGroupName]
            mcHistogram = NewStackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.histograms if histogram['group']!=dataGroupName], outputName='summedMcHistograms') 
            self.drawRatioPlot(dataHistogram, mcHistogram)

            self.pads['oben'].cd()
            theErrorGraph = ROOT.TGraphErrors(mcHistogram)
            theErrorGraph.SetFillColor(ROOT.kGray+3)
            theErrorGraph.SetFillStyle(3013)
            theErrorGraph.Draw('SAME2')
        else:
            theErrorGraph = None

        # draw legend
        self.drawSampleLegend(groupedHistograms, theErrorGraph)

        # draw various labels
        if not normalize:
            self.drawPlotTexts()

        # save to file
        for ext in self.outputFileFormats:
            outputFileName = self.outputFileTemplate.format(outputFolder=outputFolder, prefix=prefix, prefixSeparator='_' if len(prefix)>0 else '', var=self.var, ext=ext)
            c.SaveAs(outputFileName)
            if os.path.isfile(outputFileName):
                print ("INFO: saved as \x1b[34m", outputFileName, "\x1b[0m")
            else:
                print ("\x1b[31mERROR: could not save canvas to the file:", outputFileName, "\x1b[0m")

