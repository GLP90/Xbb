#!/usr/bin/env python
import pickle
import sys, os
from optparse import OptionParser
from copy import copy,deepcopy
from math import sqrt
import math
from HiggsAnalysis.CombinedLimit.DatacardParser import *
from HiggsAnalysis.CombinedLimit.ShapeTools     import *

# import ROOT with a fix to get batch mode (http://root.cern.ch/phpBB3/viewtopic.php?t=3198)
hasHelp = False
argv = sys.argv
for X in ("-h", "-?", "--help"):
    if X in argv:
        hasHelp = True
        argv.remove(X)
argv.append( '-b-' )
import ROOT
from myutils import StackMaker, BetterConfigParser

ROOT.gROOT.SetBatch(True)
ROOT.gSystem.Load("libHiggsAnalysisCombinedLimit.so")
argv.remove( '-b-' )
if hasHelp: argv.append("-h")

#CONFIGURE
parser = OptionParser()
parser.add_option("-D", "--datacard", dest="dc", default="",
                      help="Datacard to be plotted")
parser.add_option("-B", "--bin", dest="bin", default="",
                      help="DC bin to plot")
parser.add_option("-M", "--mlfit", dest="mlfit", default="",
                      help="mlfit file for nuisances")
parser.add_option("-F", "--fitresult", dest="fit", default="s",
                      help="Fit result to be used, 's' (signal+background)  or 'b' (background only), default is 's'")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
parser.add_option("-V", "--variable", dest="var", default="",
                      help="variable to be fitted")

(opts, args) = parser.parse_args(argv)

print opts

def readBestFit(theFile):
    file = ROOT.TFile(theFile)
    if file == None: raise RuntimeError, "Cannot open file %s" % theFile
    fit_s  = file.Get("fit_s")
    fit_b  = file.Get("fit_b")
    prefit = file.Get("nuisances_prefit")
    if fit_s == None or fit_s.ClassName()   != "RooFitResult": raise RuntimeError, "File %s does not contain the output of the signal fit 'fit_s'"     % args[0]
    if fit_b == None or fit_b.ClassName()   != "RooFitResult": raise RuntimeError, "File %s does not contain the output of the background fit 'fit_b'" % args[0]
    if prefit == None or prefit.ClassName() != "RooArgSet":    raise RuntimeError, "File %s does not contain the prefit nuisances 'nuisances_prefit'"  % args[0]

    isFlagged = {}
    table = {}
    fpf_b = fit_b.floatParsFinal()
    fpf_s = fit_s.floatParsFinal()
    nuiVariation = {}
    for i in range(fpf_s.getSize()):
        nuis_s = fpf_s.at(i)
        name   = nuis_s.GetName();
        nuis_b = fpf_b.find(name)
        nuis_p = prefit.find(name)
        if nuis_p != None:
            mean_p, sigma_p = (nuis_p.getVal(), nuis_p.getError())
        for fit_name, nuis_x in [('b', nuis_b), ('s',nuis_s)]:
            if nuis_p != None:
                valShift = (nuis_x.getVal() - mean_p)/sigma_p
                sigShift = nuis_x.getError()/sigma_p
                print fit_name, name
                print valShift
                nuiVariation['%s_%s'%(fit_name,name)] = [valShift,sigShift]
                #print valShift
    return nuiVariation

def getBestFitShapes(procs,theShapes,shapeNui,theBestFit,DC,setup,opts,Dict):
    b = opts.bin
    for p in procs:
        counter = 0
        nom = theShapes[p].Clone()
        for (lsyst,nofloat,pdf,pdfargs,errline) in DC.systs:
            if errline[b][p] == 0: continue
            if ("shape" in pdf):
                if shapeNui[p+lsyst] > 0.:
                    theVari = 'Up'
                else:
                    theVari = 'Down'
                bestNuiVar = theShapes[p+lsyst+theVari].Clone()
                bestNuiVar.Add(nom,-1.)
                #print p,lsyst,abs(shapeNui[p+lsyst]),bestNuiVar.Integral()
                bestNuiVar.Scale(abs(shapeNui[p+lsyst]))
                if counter == 0:
                    bestNui = bestNuiVar.Clone()
                else:
                    bestNui.Add(bestNuiVar)
                counter +=1
        nom.Add(bestNui)
        #nom.Scale(theBestFit[p])
        nom.Scale(theShapes[p].Integral()/nom.Integral()*theBestFit[p])
        nBins = nom.GetNbinsX()
        for bin in range(1,nBins+1):
            nom.SetBinError(bin,theShapes[p].GetBinError(bin))
        theShapes['%s_%s'%(opts.fit,p)] = nom.Clone()
    histos = []
    typs = []
    sigCount = 0
    signalList = ['ZH','WH']
    #signalList = ['VVb']
    for s in setup:
        if s in signalList:
            if sigCount ==0:
                Overlay=copy(theShapes[Dict[s]])
            else:
                Overlay.Add(theShapes[Dict[s]])
            sigCount += 1
        else:
            histos.append(theShapes['%s_%s'%(opts.fit,Dict[s])])
            typs.append(s)
    return histos,Overlay,typs


def drawFromDC():
    config = BetterConfigParser()
    config.read(opts.config)
    print "opts.config:",opts.config
    dataname = ''
    if 'Zmm' in opts.bin: dataname = 'Zmm'
    elif 'Zee' in opts.bin: dataname = 'Zee'
    elif 'Wmunu' in opts.bin: dataname = 'Wmn'
    elif 'Wenu' in opts.bin: dataname = 'Wen'
    elif 'Znunu' in opts.bin: dataname = 'Znn'
    elif 'Wtn' in opts.bin: dataname = 'Wtn'

    print 'Variable printing'
    print opts.var
    if(opts.var == ''):
        var = 'BDT'
        if dataname == 'Zmm' or dataname == 'Zee': var = 'BDT_Zll' 
        elif dataname == 'Wmn' or dataname == 'Wen': var = 'BDT_Wln' 
        elif dataname == 'Znn': 
            if 'HighPt' in opts.bin: var = 'BDT_ZnnHighPt'
            elif 'LowPt' in opts.bin: var = 'BDT_ZnnLowPt'
            elif 'LowCSV' in opts.bin: var = 'BDT_ZnnLowCSV'
            else: var = 'BDT_Znn'
        if dataname == '' or var == 'BDT': raise RuntimeError, "Did not recognise mode or var from %s" % opts.bin
    else:
        var = opts.var
        
    region = 'BDT'
    ws_var = config.get('plotDef:%s'%var,'relPath')
    ws_var = ROOT.RooRealVar(ws_var,ws_var,-1.,1.)
    blind = eval(config.get('Plot:%s'%region,'blind'))
    Stack=StackMaker(config,var,region,True)

    if 'LowPt' in opts.bin or 'ch1_Wenu' == opts.bin or 'ch2_Wmunu' == opts.bin:
        print 'Niklas %s' %opts.bin
        Stack.addFlag2 = 'Low p_{T}(V)'
    elif 'MedPt' in opts.bin or 'ch1_Wenu2' == opts.bin or 'ch2_Wmunu2' == opts.bin:
        Stack.addFlag2 = 'Intermediate p_{T}(V)'
    elif 'HighPt' in opts.bin or 'ch1_Wenu3' == opts.bin or 'ch2_Wmunu3' == opts.bin:
        Stack.addFlag2 = 'High p_{T}(V)'
    else:
        Stack.addFlag2 = ''

    preFit = False
    addName = 'PostFit_%s' %(opts.fit)
    if not opts.mlfit:
        addName = 'PreFit'
        preFit = True

    Stack.options['pdfName'] = '%s_%s_%s.pdf'  %(var,opts.bin,addName)

    log = eval(config.get('Plot:%s'%region,'log'))

    setup = config.get('Plot_general','setup').split(',')
    if dataname == 'Zmm' or dataname == 'Zee': 
        try:
            setup.remove('W1b')
            setup.remove('W2b')
            setup.remove('Wlight')
            setup.remove('WH')
        except:
            print '@INFO: Wb / Wligh / WH not present in the datacard'
    if not dataname == 'Znn' and 'QCD' in setup: 
        setup.remove('QCD')
    Stack.setup = setup

    Dict = eval(config.get('LimitGeneral','Dict'))
    lumi = eval(config.get('Plot_general','lumi'))
    
    options = copy(opts)
    options.dataname = "data_obs"
    options.mass = 0
    options.format = "%8.3f +/- %6.3f"
    options.channel = opts.bin
    options.excludeSyst = []
    options.norm = False
    options.stat = False
    options.bin = True # fake that is a binary output, so that we parse shape lines
    options.out = "tmp.root"
    options.fileName = args[0]
    options.cexpr = False
    options.fixpars = False
    options.libs = []
    options.verbose = 0
    options.poisson = 0
    options.nuisancesToExclude = []
    options.noJMax = None
    theBinning = ROOT.RooFit.Binning(Stack.nBins,Stack.xMin,Stack.xMax)

    file = open(opts.dc, "r")
    os.chdir(os.path.dirname(opts.dc))
    DC = parseCard(file, options)
    if not DC.hasShapes: DC.hasShapes = True
    MB = ShapeBuilder(DC, options)
    theShapes = {}
    theSyst = {}
    nuiVar = {}
    if opts.mlfit:
        nuiVar = readBestFit(opts.mlfit)
    if not opts.bin in DC.bins: raise RuntimeError, "Cannot open find %s in bins %s of %s" % (opts.bin,DC.bins,opts.dc)
    for b in DC.bins:
        if options.channel != None and (options.channel != b): continue
        exps = {}
        expNui = {}
        shapeNui = {}
        reducedShapeNui = {}
        for (p,e) in DC.exp[b].items(): # so that we get only self.DC.processes contributing to this bin
            exps[p] = [ e, [] ]
            expNui[p] = [ e, [] ]
        for (lsyst,nofloat,pdf,pdfargs,errline) in DC.systs:
            if pdf in ('param', 'flatParam'): continue
            # begin skip systematics
            skipme = False
            for xs in options.excludeSyst:
                if re.search(xs, lsyst): 
                    skipme = True
            if skipme: continue
            # end skip systematics
            counter = 0
            for p in DC.exp[b].keys(): # so that we get only self.DC.processes contributing to this bin
                if errline[b][p] == 0: continue
                if p == 'QCD' and not 'QCD' in setup: continue
                if pdf == 'gmN':
                    exps[p][1].append(1/sqrt(pdfargs[0]+1));
                elif pdf == 'gmM':
                    exps[p][1].append(errline[b][p]);
                elif type(errline[b][p]) == list: 
                    kmax = max(errline[b][p][0], errline[b][p][1], 1.0/errline[b][p][0], 1.0/errline[b][p][1]);
                    exps[p][1].append(kmax-1.);
                elif pdf == 'lnN':
                     lnNVar = max(errline[b][p], 1.0/errline[b][p])-1.
                     if not nuiVar.has_key('%s_%s'%(opts.fit,lsyst)):
                         nui = 0.
                     else:
                        nui= nuiVar['%s_%s'%(opts.fit,lsyst)][0]
                        lnNVar = lnNVar*nuiVar['%s_%s'%(opts.fit,lsyst)][1]
                     exps[p][1].append(lnNVar)
                     expNui[p][1].append(abs(1-errline[b][p])*nui);
                elif ("shape" in pdf):
                    #print 'shape %s %s: %s'%(pdf,p,lsyst)
                    s0 = MB.getShape(b,p)
                    sUp   = MB.getShape(b,p,lsyst+"Up")
                    sDown = MB.getShape(b,p,lsyst+"Down")
                    if (s0.InheritsFrom("RooDataHist")):
                        s0 = ROOT.RooAbsData.createHistogram(s0,p,ws_var,theBinning)
                        s0.SetName(p)
                        sUp = ROOT.RooAbsData.createHistogram(sUp,p+lsyst+'Up',ws_var,theBinning)
                        sUp.SetName(p+lsyst+'Up')
                        sDown = ROOT.RooAbsData.createHistogram(sDown,p+lsyst+'Down',ws_var,theBinning)
                        sDown.SetName(p+lsyst+'Down')
                    theShapes[p] = s0.Clone()
                    theShapes[p+lsyst+'Up'] = sUp.Clone()
                    theShapes[p+lsyst+'Down'] = sDown.Clone()
                    if not nuiVar.has_key('%s_%s'%(opts.fit,lsyst)):
                        nui = 0.
                        reducedNui = 1.
                    else:
                        nui= nuiVar['%s_%s'%(opts.fit,lsyst)][0]
                        reducedNui= nuiVar['%s_%s'%(opts.fit,lsyst)][1]
                    shapeNui[p+lsyst] = nui
                    reducedShapeNui[lsyst] = reducedNui
                    if not 'CMS_vhbb_stat' in lsyst:
                        if counter == 0:
                            theSyst[lsyst] = s0.Clone() 
                            theSyst[lsyst+'Up'] = sUp.Clone() 
                            theSyst[lsyst+'Down'] = sDown.Clone() 
                        else:
                            theSyst[lsyst].Add(s0)
                            theSyst[lsyst+'Up'].Add(sUp.Clone())
                            theSyst[lsyst+'Down'].Add(sDown.Clone()) 
                        counter += 1

    procs = DC.exp[b].keys(); procs.sort()
    if not 'QCD' in setup and 'QCD' in procs:
        procs.remove('QCD')
    if not 'W2b' in setup and 'WjHF' in procs:
        procs.remove('WjHF')
    if not 'Wlight' in setup and 'WjLF' in procs:
        procs.remove('WjLF')
    fmt = ("%%-%ds " % max([len(p) for p in procs]))+"  "+options.format;
    #Compute norm uncertainty and best fit
    theNormUncert = {}
    theBestFit = {}
    for p in procs:
        relunc = sqrt(sum([x*x for x in exps[p][1]]))
        print fmt % (p, exps[p][0], exps[p][0]*relunc)
        theNormUncert[p] = relunc
        absBestFit = sum([x for x in expNui[p][1]])
        theBestFit[p] = 1.+absBestFit
    
    histos = []
    typs = []

    setup2=copy(setup)

    shapesUp = [[] for _ in range(0,len(setup2))]
    shapesDown = [[] for _ in range(0,len(setup2))]
    
    sigCount = 0
    signalList = ['ZH','WH']
    #signalList = ['VVb']
    for p in procs:
        b = opts.bin
        for s in setup:
            if not Dict[s] == p: continue
            if s in signalList:
                if sigCount ==0:
                    Overlay=copy(theShapes[Dict[s]])
                else:
                    Overlay.Add(theShapes[Dict[s]])
                sigCount += 1
            else:
                histos.append(theShapes[Dict[s]])
                typs.append(s)
            for (lsyst,nofloat,pdf,pdfargs,errline) in DC.systs:
                if errline[b][p] == 0: continue
                if ("shape" in pdf) and not 'CMS_vhbb_stat' in lsyst:
                    print 'syst %s'%lsyst
                    shapesUp[setup2.index(s)].append(theShapes[Dict[s]+lsyst+'Up'])
                    shapesDown[setup2.index(s)].append(theShapes[Dict[s]+lsyst+'Down'])

    #-------------
    #Compute absolute uncertainty from shapes
    counter = 0
    for (lsyst,nofloat,pdf,pdfargs,errline) in DC.systs:
        sumErr = 0
        for p in procs:
            sumErr += errline[b][p]
        if ("shape" in pdf) and not 'CMS_vhbb_stat' in lsyst and not sumErr == 0:
            theSystUp = theSyst[lsyst+'Up'].Clone()
            theSystUp.Add(theSyst[lsyst].Clone(),-1.)
            theSystUp.Multiply(theSystUp)
            theSystDown = theSyst[lsyst+'Down'].Clone()
            theSystDown.Add(theSyst[lsyst].Clone(),-1.)
            theSystDown.Multiply(theSystDown)
            theSystUp.Scale(reducedShapeNui[lsyst])
            theSystDown.Scale(reducedShapeNui[lsyst])
            if counter == 0:
                theAbsSystUp = theSystUp.Clone()
                theAbsSystDown = theSystDown.Clone()
            else:
                theAbsSystUp.Add(theSystUp.Clone())
                theAbsSystDown.Add(theSystDown.Clone())
            counter +=1
    
    #-------------
    #Best fit for shapes
    if not preFit:
        histos, Overlay, typs = getBestFitShapes(procs,theShapes,shapeNui,theBestFit,DC,setup,opts,Dict)
    
    counter = 0
    errUp=[]
    total=[]
    errDown=[]
    nBins = histos[0].GetNbinsX()
    print 'total bins %s'%nBins
    Error = ROOT.TGraphAsymmErrors(histos[0])
    theTotalMC = histos[0].Clone()
    for h in range(1,len(histos)):
        theTotalMC.Add(histos[h])
    
    total = [[]]*nBins
    errUp = [[]]*nBins
    errDown = [[]]*nBins
    for bin in range(1,nBins+1):
        binError = theTotalMC.GetBinError(bin)
        if math.isnan(binError):
            binError = 0.
        total[bin-1]=theTotalMC.GetBinContent(bin)
        #Stat uncertainty of the MC outline
        errUp[bin-1] = [binError]
        errDown[bin-1] = [binError]
        #Relative norm uncertainty of the individual MC
        for h in range(0,len(histos)):
            errUp[bin-1].append(histos[h].GetBinContent(bin)*theNormUncert[histos[h].GetName()])
            errDown[bin-1].append(histos[h].GetBinContent(bin)*theNormUncert[histos[h].GetName()])
    #Shape uncertainty of the MC
    for bin in range(1,nBins+1):
        #print sqrt(theSystUp.GetBinContent(bin))
        errUp[bin-1].append(sqrt(theAbsSystUp.GetBinContent(bin)))
        errDown[bin-1].append(sqrt(theAbsSystDown.GetBinContent(bin)))
    

    #Add all in quadrature
    totErrUp=[sqrt(sum([x**2 for x in bin])) for bin in errUp]
    totErrDown=[sqrt(sum([x**2 for x in bin])) for bin in errDown]

    #Make TGraph with errors
    for bin in range(1,nBins+1):
        if not total[bin-1] == 0:
            point=histos[0].GetXaxis().GetBinCenter(bin)
            Error.SetPoint(bin-1,point,1)
            Error.SetPointEYlow(bin-1,totErrDown[bin-1]/total[bin-1])
            print 'down %s'%(totErrDown[bin-1]/total[bin-1])
            Error.SetPointEYhigh(bin-1,totErrUp[bin-1]/total[bin-1])
            print 'up   %s'%(totErrUp[bin-1]/total[bin-1])

    #-----------------------
    #Read data
    data0 = MB.getShape(opts.bin,'data_obs')
    if (data0.InheritsFrom("RooDataHist")):
        data0 = ROOT.RooAbsData.createHistogram(data0,'data_obs',ws_var,theBinning)
        data0.SetName('data_obs')
    datas=[data0]
    datatyps = [None]
    datanames=[dataname] 


    if blind and 'BDT' in var:
        for bin in range(10,datas[0].GetNbinsX()+1):
            datas[0].SetBinContent(bin,0)

    histos.append(copy(Overlay))
    if 'ZH' in signalList and 'WH' in signalList:
        typs.append('VH')
        if 'ZH' in Stack.setup: Stack.setup.remove('ZH')
        if 'WH' in Stack.setup: Stack.setup.remove('WH')
        Stack.setup.insert(0,'VH')
    elif 'ZH' in signalList:
        typs.append('ZH')
    elif 'WH' in signalList:
        typs.append('WH')
    elif 'VVb' in signalList:
        typs.append('VVb')
    print Stack.setup

    Stack.histos = histos
    Stack.typs = typs
    Stack.datas = datas
    Stack.datatyps = datatyps
    Stack.datanames= datanames
    Stack.overlay = [Overlay]
    Stack.AddErrors=Error
    if dataname == 'Wtn': 
        lumi = 18300.
    Stack.lumi = lumi
    Stack.doPlot()

    print 'i am done!\n'
#-------------------------------------------------


if __name__ == "__main__":
    drawFromDC()
    sys.exit(0)
