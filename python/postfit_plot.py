#!/usr/bin/env python
from __future__ import print_function
from optparse import OptionParser
from collections import defaultdict
import ROOT
ROOT.gROOT.SetBatch(True)

from myutils.NewStackMaker import NewStackMaker as StackMaker
from myutils.samplesclass import Sample
import os,sys
import array
import math

class PostfitPlotter(object):

    def __init__(self, config, region, vars=None, directory="shapes_fit_s", title=None, blind=True):
        self.config = config
        self.region = region if type(region) == list else [region]
        self.fitRegions = eval(self.config.get('Fit', 'regions'))
        self.dcRegion = [self.fitRegions[x] for x in self.region] 
        self.var = "postfitDNN"
        self.directory = directory
        self.shapesFile = None
        self.plotPath = config.get('Directories', 'plotpath')
        self.title = None # "CMS #scale[0.8]{work in progress}"
        self.blindBins = []
        self.blind = blind
        self.plotText = [""]
        if self.config.has_option('Fit', 'plotText'):
            self.plotText = eval(self.config.get('Fit', 'plotText'))

        self.x_axis = None
        if self.config.has_option('Fit:'+self.region[0], 'x_axis'):
            if  isinstance(eval(self.config.get('Fit:'+self.region[0], 'x_axis')), list):
                self.x_axis = array.array('d', eval(self.config.get('Fit', 'x_axis')))
            else: 
                x_axis = self.config.get('Fit:'+self.region[0], 'x_axis')
                x_axis_list = x_axis.split(',')
                nbins = int(x_axis_list[0])
                x_low = float(x_axis_list[1])
                x_high = float(x_axis_list[2])
                import numpy
                self.x_axis = array.array('d', numpy.arange(x_low, x_high,(x_high-x_low)/(nbins)))
                self.x_axis.append(x_high)
                print(self.x_axis)

        print('region is', self.region[0])
        if self.config.has_section('Fit:'+self.region[0]):
            if self.config.has_option('Fit:'+self.region[0], 'var'):
                self.var = self.config.get('Fit:'+self.region[0], 'var')
            if self.blind and self.config.has_option('Fit:'+self.region[0], 'blindBins'):
                self.blindBins = eval(self.config.get('Fit:'+self.region[0], 'blindBins'))
            if self.config.has_option('Fit:'+self.region[0], 'plotText'):
                self.plotText += eval(self.config.get('Fit:'+self.region[0],'plotText'))
        #print(self.plotText)
        #sys.exit()

    def prepare(self):
        self.dcDict = eval(self.config.get('LimitGeneral','Dict'))
        self.reverseDcDict = {v:k for k,v in self.dcDict.items()}
        self.regionDict = eval(self.config.get('Fit', 'regions'))
        self.reverseRegionDict = {v:k for k,v in self.regionDict.items()}
        self.setup = eval(self.config.get('LimitGeneral','setup'))
        self.setupSignals = eval(self.config.get('LimitGeneral','setupSignals')) if self.config.has_option('LimitGeneral','setupSignals') else []

        shapesFileName = self.config.get('Fit', 'FitDiagnosticsDump')
        self.shapesFile = ROOT.TFile.Open(shapesFileName, "READ")
        print("REV:", self.reverseDcDict)

    # process is datacard name convention, convert it back to Xbb process convention if necessary
    def getNameFromDcname(self, process):
        return self.reverseDcDict[process] if process in self.reverseDcDict else process

    def getDcnameFromName(self, processName):
        return self.dcDict[processName]

    def getProcesses(self):
        return self.setup

    def getHistogramName(self, process):
        processName = self.getNameFromDcname(process) 
        
        # use pre-fit signal strength for plotting if blind
        if self.blind and processName in self.setupSignals:
            print("INFO: \x1b[31mBLIND: prefit shapes are plotted for signal!\x1b[0m")
            histogramName = 'shapes_prefit/{dcRegion}/' + process
        else:
            histogramName = self.directory + '/{dcRegion}/' + process

        print("DEBUG: get shape ", histogramName)
        return histogramName

    def getShape(self, process):

        histogramNameTemplate = self.getHistogramName(process)
        histograms = []
        histogramBins = []
        for x in self.dcRegion:
            histograms.append(self.shapesFile.Get(histogramNameTemplate.format(dcRegion=x)))
            r = self.reverseRegionDict[x] 
            if self.config.has_section('Fit:'+r) and self.config.has_option('Fit:'+r, 'nBins'):
                nBins = eval(self.config.get('Fit:'+r, 'nBins'))
            else:
                nBins = histograms[-1].GetXaxis().GetNbins()
            print("NBINS:", nBins, x, r)
            histogramBins.append(nBins)
        #histograms = [self.shapesFile.Get(histogramNameTemplate.format(dcRegion=x)) for x in self.dcRegion]

        if len(histograms) == 1:
            histogram = histograms[0]
        else:
            nBinsTotal = sum(histogramBins)
            histogram = ROOT.TH1D("h1", "", nBinsTotal, 0, nBinsTotal)
            histogram.SetDirectory(0)

            iBin = 1
            if isinstance(histograms[0], ROOT.TGraphAsymmErrors):
                histogram = ROOT.TGraphAsymmErrors()
                tlist = ROOT.TList()
                for i,h in enumerate(histograms):
                    h.Set(histogramBins[i])
                    tlist.Add(h)
                histogram.Merge(tlist)
                offset = 0
                for i in range(histogram.GetN()):
                    p_x = array.array('d', [0.0])
                    p_y = array.array('d', [0.0])
                    histogram.GetPoint(i, p_x, p_y)
                    if i == 0:
                        offset = p_x[0]
                    print("P:",i,p_x[0],p_y[0],"-->", i, p_y[0])
                    histogram.SetPoint(i, i + offset, p_y[0])
            else:
                for i,h in enumerate(histograms):
                    if h:
                        for n in range(histogramBins[i]):
                            histogram.SetBinContent(iBin, h.GetBinContent(1+n))
                            histogram.SetBinError(iBin, h.GetBinError(1+n))
                            iBin += 1

        #histogram = self.shapesFile.Get(histogramName)
        #print("DEBUG: -->", histogram, histogram.Integral())
        return histogram

    def rebinShape(self,histogram):
        histogram.SaveAs("before.root")
        if isinstance(histogram, ROOT.TGraphAsymmErrors):
            x_axis = self.x_axis
            p_x = array.array('d', [0.0])
            p_y = array.array('d', [0.0])
            nbins = histogram.GetN()
            #if nbins != len(x_axis)-1:
            #    print('@ERROR: x_axis has a different number of bins than the shape')
            #    print(nbins)
            #    sys.exit()
            
            for i in range(len(x_axis)-1):
                x = (x_axis[i] + x_axis[i+1])/2
                x_low = x - x_axis[i] 
                x_high = x_axis[i+1] -x
                histogram.GetPoint(i, p_x, p_y)
                histogram.SetPoint(i, x, p_y[0])
                histogram.SetPointEXlow(i, x_low)
                histogram.SetPointEXhigh(i, x_high)
            histogram.SaveAs("after.root")
            return histogram
        else:
            h = ROOT.TH1D(histogram.GetName(),histogram.GetName(), len(self.x_axis)-1, self.x_axis)
            for b in range(1,histogram.GetXaxis().GetNbins()+1):
                content = histogram.GetBinContent(b)
                h.SetBinContent(b, content)
            #h.SaveAs("after.root")
            return h

    def run(self):

        self.stack = StackMaker(self.config, self.var, self.region[0], True, self.setup, '_', title=self.title)
        self.stack.setPlotText(self.plotText)

        # add MC
        print("INFO: setup = \x1b[31m", self.setup, "\x1b[0m")
        for process in self.setup:

            if self.x_axis:
                histogram = self.rebinShape(self.getShape(self.dcDict[process]))
            else: 
                histogram = self.getShape(self.dcDict[process])
            if histogram:
                self.stack.histograms.append({
                        'name': process, 
                        'histogram': histogram, 
                        'group': process
                    })
            else:
                print("\x1b[31mINFO: empty: ",process,"\x1b[0m")
        
        # dump S/B
        #shapeS = self.getShape("total_signal")
        #shapeB = self.getShape("total_background")
        shapeS = StackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.stack.histograms if histogram['group'] in self.setupSignals], outputName='totalSignal') 
        shapeB = StackMaker.sumHistograms(histograms=[histogram['histogram'] for histogram in self.stack.histograms if histogram['group'] not in self.setupSignals], outputName='totalBackground') 
        print("name:", shapeB.GetName(), " / ", self.directory)
        print("file:", self.shapesFile)
        print("shape:", shapeS, shapeB)
        print(self.region,"-"*40)
        print( ("bin").ljust(5), ("S").ljust(8), ("B").ljust(8))
        sum_s_over_sqrtb = 0.0
        sum_s = 0.0
        sum_b = 0.0
        sum_med_z_a = 0.0
        for i in range(shapeS.GetXaxis().GetNbins()):
            s = shapeS.GetBinContent(1+i)
            b = shapeB.GetBinContent(1+i)
            print( ("%d"%i).ljust(5), ("%1.2f"%s).ljust(8), ("%1.2f"%b).ljust(8))

            sum_s_over_sqrtb += s*s/b if b>0 else 0
            sum_s += s
            sum_b += b
            sum_med_z_a += 2.0* ( (s+b) * math.log(1.0 + s/b) - s) if s > 0 else 0.0
        sum_s_over_sqrtb = math.sqrt(sum_s_over_sqrtb)

        if sum_med_z_a >= 0.:
            sum_med_z_a = math.sqrt(sum_med_z_a)
        print("TOTAL: s/sqrt(b):", "%1.3f"%sum_s_over_sqrtb, " s:",sum_s, " b:",sum_b, " med[Z]=sqrt(q_A)=", sum_med_z_a)
        
        # add DATA
        if self.x_axis:
            dataHistogram = self.rebinShape(self.getShape("data"))
        else:
            dataHistogram = self.getShape("data")
        pointX = array.array('d', [0.0, 0.0])
        pointY = array.array('d', [0.0, 0.0])

        # blind last few bins
        dataIntegral = 0
        for i in range(dataHistogram.GetN()):
            dataHistogram.GetPoint(i, pointX, pointY)
            dataIntegral += pointY[0]
            if int(pointX[0]+1) in self.blindBins:
                dataHistogram.SetPoint(i, -100, -100)
            if self.x_axis and  len(self.blindBins) > 0 and i >= min(self.blindBins):
                dataHistogram.SetPoint(i, -100, -100)

        print("DATA:", dataIntegral, "MC:", sum_s+sum_b)

        # style data
        dataHistogram.SetMarkerColor(ROOT.kBlack)
        dataHistogram.SetMarkerStyle(20)

        self.stack.histograms.append({
                'name': 'DATA', 
                'histogram': dataHistogram,
                'group': 'DATA'
            })

        # draw
        self.stack.Draw(outputFolder=self.plotPath, prefix='{region}__{var}_'.format(region=self.region[0], var=self.directory))


if __name__ == "__main__":
    # read arguments
    argv = sys.argv
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                              help="Verbose mode.")
    parser.add_option("-C", "--config", dest="config", default=[], action="append",
                          help="configuration file")
    parser.add_option("-r","--regions", dest="regions", default='',
                          help="cut region identifiers, separated by comma")
    parser.add_option("-t","--type", dest="fitType", default='',
                          help="shapes_prefit, shapes_fit_b, shapes_fit_s")
    parser.add_option("-u", "--unblind", action="store_true", dest="unblind", default=False,
                              help="Unblind")

    (opts, args) = parser.parse_args(argv)
    if opts.config == "":
            opts.config = ["config"]

    # Import after configure to get help message
    from myutils import BetterConfigParser, mvainfo, ParseInfo
    config = BetterConfigParser()
    config.read(opts.config)

    if len(opts.fitType) < 1:
        if config.has_option('Fit','FitType'):
            opts.fitType = config.get('Fit','FitType')
        else:
            opts.fitType = "shapes_prefit"

    # run plotter
    if len(opts.regions) < 1 or opts.regions.strip() == 'None':
        regions = eval(config.get('Fit', 'regions')).keys()
    else:
        regions = opts.regions.strip().split(',')
        for i in range(len(regions)):
            if '+' in regions[i]:
                regions[i] = regions[i].split('+')
        print("REGIONS:", regions)
    
    scaleFactorTable = []
    plotCommands = []
    for region in regions:
        print("INFO: region:", region)
        plotter = PostfitPlotter(config=config, region=region, directory=opts.fitType, blind=not opts.unblind)
        plotter.prepare()
        plotter.run()


        # COMPUTE effective scale factors
        if opts.fitType == 'shapes_fit_s':
            plotter_prefit = PostfitPlotter(config=config, region=region, directory="shapes_prefit", blind=not opts.unblind)
            plotter_prefit.prepare()
        
            regionSF = defaultdict(lambda: 1.0)
            #regionSF = {'TT': 1.0, 'ZJets_0b': 1.0, 'ZJets_1b': 1.0, 'ZJets_2b': 1.0,'WJets_0b': 1.0, 'WJets_1b': 1.0, 'WJets_2b': 1.0}

            for process in plotter.getProcesses():
                try:
                    histogram_postfit = plotter.getShape(plotter.getDcnameFromName(process))
                    histogram_prefit  = plotter_prefit.getShape(plotter.getDcnameFromName(process))

                    nBins_prefit = histogram_prefit.GetXaxis().GetNbins()
                    nBins_postfit = histogram_postfit.GetXaxis().GetNbins()
                    assert nBins_prefit == nBins_postfit
                    histogram_postfit.Rebin(nBins_postfit)
                    histogram_prefit.Rebin(nBins_prefit)
                    
                    histogram_postfit.Divide(histogram_prefit)

                    scaleFactorTable.append("{region} {process} prefit/postfit = {scale} +/- {error}".format(region=region, process=process, scale=histogram_postfit.GetBinContent(1), error=histogram_postfit.GetBinError(1))) 
                    regionSF[process] = histogram_postfit.GetBinContent(1)
                except Exception as e:
                    print("WARNING:", e)

            # VHbb specific plot commands for simplifity
            try:
                plotCommand = "./submit.py -J runplot --parallel=8 --regions '{region}' --set='General.SF_TT={SF[TT]};General.SF_ZJets=[{SF[ZJets_0b]},{SF[ZJets_1b]},{SF[ZJets_2b]}];General.SF_WJets=[{SF[WJets_0b]},{SF[WJets_1b]},{SF[WJets_2b]}]'".format(region=region, SF=regionSF)
                plotCommands.append(plotCommand)
            except Exception as e:
                print("WARNING:", e)

    # PRINT effective scale factors
    if opts.fitType == 'shapes_fit_s':
        print("INFO: --------------------------------------------------------------------------------")
        print("INFO: effective scale factors (including combined effects of all uncertainties)")
        print("INFO: --------------------------------------------------------------------------------")

        for line in scaleFactorTable:
            print("INFO:", line)
        print("INFO: --------------------------------------------------------------------------------")
        for line in plotCommands:
            print("", line)
        print("INFO: --------------------------------------------------------------------------------")

