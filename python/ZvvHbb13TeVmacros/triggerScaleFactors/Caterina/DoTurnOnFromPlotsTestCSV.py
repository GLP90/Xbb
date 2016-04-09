import ROOT
import copy
from math import *
import array

f = open('fittedFunctions.h', 'w')

ROOT.gROOT.LoadMacro("tdrstyleTrigger.C")
ROOT.setTDRStyle()

minTurnOn   = 0
maxTurnOn   = 1.05

minRatio    = 0.8
maxRatio    = 1.2

functionMin = 80
functionMax = 500

ped = "function"

title = "aaa"

def getTitle(fileName):
    file_ = ROOT.TFile.Open(fileName)
    file_.cd()
    name = file_.GetListOfKeys().First().GetName()
    canvas =  file_.Get(name)
    pad =  canvas.GetPrimitive("unten")
    title =  pad.GetPrimitive("Ratio").GetXaxis().GetTitle()
    return title

def DivideTGraph(num,den):
    Ns_den   = den.GetN()
    Xs_den   = den.GetX()
    Ys_den   = den.GetY()
    EXLs_den = den.GetEXlow()
    EXHs_den = den.GetEXhigh()
    EYLs_den = den.GetEYlow()
    EYHs_den = den.GetEYhigh()

    print "den.GetN()",den.GetN()
    print "num.GetN()",num.GetN()

    Ys_num   = num.GetY()
    EYLs_num = num.GetEYlow()
    EYHs_num = num.GetEYhigh()

    print "DivideTGraph: new"

    bins   = [ i for i in range( Ns_den) if Ys_den[i]>0]

    print "Xs_den",Xs_den
    Xs_new   = [ Xs_den[i] for i in bins]
    print "Xs_new",Xs_new
    Ys_new   = [ Ys_num[i]/(Ys_den[i]) for i in bins]
    EXLs_new = [ EXLs_den[i] for i in bins]
    EXHs_new = [ EXHs_den[i] for i in bins]
    [ EYLs_num[i] for i in bins]
    [ ((EYLs_num[i]/(Ys_num[i]+1E-3))**2) for i in bins]
    [ Ys_new[i]*sqrt((EYLs_num[i]/(Ys_num[i]+1E-3))**2) for i in bins]
    EYLs_new = [ Ys_new[i]*sqrt((EYLs_num[i]/(Ys_num[i]+1E-3))**2+(EYHs_den[i]/(Ys_den[i]+1E-3))**2) for i in bins]
    EYHs_new = [ Ys_new[i]*sqrt((EYHs_num[i]/(Ys_num[i]+1E-3))**2+(EYLs_den[i]/(Ys_den[i]+1E-3))**2) for i in bins]

    print "DivideTGraph: len"

    n = len(Xs_new)

    print "DivideTGraph: array"

    Xs_new = array.array('f',Xs_new)
    Ys_new = array.array('f',Ys_new)
    EXLs_new = array.array('f',EXLs_new)
    EXHs_new = array.array('f',EXHs_new)
    EYLs_new = array.array('f',EYLs_new)
    EYHs_new = array.array('f',EYHs_new)

    print "DivideTGraph: ratio"

    ratio = ROOT.TGraphAsymmErrors(n, Xs_new, Ys_new, EXLs_new, EXHs_new, EYLs_new, EYHs_new)
    print "DivideTGraph: done"

    return ratio

def makeHistos(var="MaxIf$(Jet_btagCSV,Jet_pt>30)",trigger="ntrgObjects_hltCSV0p72L3>0",preselection="HLT_BIT_HLT_PFMET90_PFMHT90_IDTight_v",binning=(100,0,1),fileName=""):
    tree = ROOT.TChain("tree")
    tree.Add(fileName)
    print "fileName=",fileName
    print "var=",var
    print "trigger=",trigger
    print "preselection=",preselection
    print "binning=",str(binning)
    tree.Draw(var+">>num"+str(binning),str(preselection+"&&"+trigger))
    print "Draw:\t",var+">>num"+str(binning),str(preselection+"&&"+trigger)
    num = ROOT.gDirectory.Get("num")
    num = copy.copy(num)
    tree.Draw(var+">>den"+str(binning),str(preselection))
    print "Draw:\t",var+">>den"+str(binning),str(preselection)
    den = ROOT.gDirectory.Get("den")
    den = copy.copy(den)
    print "num,den = ",num.Integral(),den.Integral()
    return num,den



def getMCAndData(fileName):
    file_ = ROOT.TFile.Open(fileName)
    file_.cd()
    name = file_.GetListOfKeys().First().GetName()
    canvas =  file_.Get(name)
    pad =  canvas.GetPrimitive("oben")
    mystack =  pad.GetPrimitive(name)
    MC_tmp =  mystack.GetStack().Last()
    data_tmp =  pad.GetPrimitive("noData")
    MC =  MC_tmp.Clone("MC")
    data =  data_tmp.Clone("data")
    MC.SetTitle("MC")
    data.SetTitle("data")
    MC.GetXaxis().SetTitle(title)
    data.GetXaxis().SetTitle(title)
    MC.SetMarkerStyle(20)
    data.SetMarkerStyle(20)
    MC.SetMarkerColor(ROOT.kBlack)
    data.SetMarkerColor(ROOT.kBlack)
    MC = copy.copy(MC)
    data = copy.copy(data)
    file_.Close()
    return MC,data

def doRatio(num, den, option=""):
#    mratio =  den.Clone("mratio")
#    mratio.SetTitle("Ratio")
#    mratio.Reset()
#    if option is "b":
#        mratio.Divide(num,den,1,1,"b")
#    else:
#        mratio.Divide(num,den)
#    return mratio
        mratio = ROOT.TGraphAsymmErrors()
        mratio.SetMarkerColor(ROOT.kBlack)
        mratio.SetLineColor(ROOT.kBlack)
        mratio.SetName("ratio")
        mratio.GetXaxis().SetTitle(title)
#        mratio = histo.Clone(triggerName+"_eff")
#        mratio.Divide(histo,inclusive,1.,1.,"B")
#        mratio.Divide(histo,inclusive,1.,1.,"cl=0.683 b(1,1) mode")
#        print num.GetNbinsX(),num.GetXaxis().GetXmin(),num.GetXaxis().GetXmax()
#        print den.GetNbinsX(),den.GetXaxis().GetXmin(),den.GetXaxis().GetXmax()
        for i in range(num.GetNbinsX()):print num.GetBinLowEdge(i),
        print ""
        for i in range(den.GetNbinsX()): print den.GetBinLowEdge(i),
        print ""

        for i in range(den.GetNbinsX()+2):
            if den.GetBinContent(i)<=0:
                den.SetBinError(i,1.)
                den.SetBinContent(i,0)
                num.SetBinContent(i,0)
#        for i in range(num.GetNbinsX()+2):
#            if num.GetBinContent(i)<=0:
#                num.SetBinError(i,10.)
#                num.SetBinContent(i,1.E-7)
        for i in range(den.GetNbinsX()+2):
            if num.GetBinContent(i)>den.GetBinContent(i):
                print "WARNING!"
                print num.GetBinContent(i),den.GetBinContent(i)
                num.SetBinContent(i,den.GetBinContent(i))
#            num.SetBinContent(i,num.GetBinContent(i))
#            den.SetBinContent(i,den.GetBinContent(i))

        mratio.Divide(num,den,"cl=0.683 b(1,1) mode")
        print "End ratio. bins:",mratio.GetN()," num:",num.GetNbinsX()," den:",den.GetNbinsX()
        return mratio

def confidenceInterval(graph, function):
    fit = function.Clone("fit")
    fitUp = function.Clone("fitUp")
    fitUp.SetLineColor(ROOT.kRed)
    fitUp.SetLineStyle(2)
    fitDown = function.Clone("fitDown")
    fitDown.SetLineStyle(2)
    print "Fit1"
    graph.Fit(fit,"","",fit.GetXmin(),fit.GetXmax())
    print "Fit2"
    graph.Fit(fit,"","",fit.GetXmin(),fit.GetXmax()) #was WW
    print "Fit3"
    graph.Fit(fit,"","",fit.GetXmin(),fit.GetXmax())
    parameters = [0]*function.GetNpar()
    for i in range(len(parameters)):
        parameters[i] = fit.GetParameter(i)

    parametersUp = parameters[:]
    parametersDown = parameters[:]

    looseRange=10.
    tightRange=10.

    print "Up/down fit"

    ## FixParameters
    for i in range(len(parameters)):
        fit.ReleaseParameter(i)
#        if i in [0]: #  x0 can go down
#            pass
#        elif i in [3]: # global efficiency can go up
#            pass
        if i in [0,2,3]: #  x0 can go down
            pass
        else: # fix the other parameters
            fit.FixParameter( i, parameters[i] )
    fitResult = graph.Fit(fit,"SEV0","",fit.GetXmin(),fit.GetXmax())
    ## Up
    for i in range(len(parameters)):
        print "XXXXXXXXX"
        print "i=",i
        print fitResult.UpperError(i)
        print fitResult.LowerError(i)

        parameters[i] = fit.GetParameter(i)
        nsigma = 2
        if i in [0]: #  x0 can go down
            parametersUp[i] = fit.GetParameter(i) + fitResult.LowerError(i)*nsigma
            parametersDown[i] = fit.GetParameter(i) + fitResult.UpperError(i)*nsigma
        elif i in [1]: # check-me!
            parametersUp[i] = fit.GetParameter(i) + fitResult.UpperError(i)*nsigma
            parametersDown[i] = fit.GetParameter(i) + fitResult.LowerError(i)*nsigma
        elif i in [2]: # check-me!
            parametersUp[i] = fit.GetParameter(i) + fitResult.LowerError(i)*nsigma
            parametersDown[i] = fit.GetParameter(i) + fitResult.UpperError(i)*nsigma
        elif i in [3]: # global efficiency can go up
            parametersUp[i] = fit.GetParameter(i) + fitResult.LowerError(i)*nsigma
            parametersDown[i] = fit.GetParameter(i) + fitResult.UpperError(i)*nsigma
        else: # fix the other parameters
            parametersUp[i] = fit.GetParameter(i)
            parametersDown[i] = fit.GetParameter(i)

        print "fit.GetParameter(1)*fit.GetParameter(2)"
        print fit.GetParameter(1)*fit.GetParameter(2)
        print "(fit.GetParameter(1)*fit.GetParameter(2))<0"
        print (fit.GetParameter(1)*fit.GetParameter(2))<0
        print "fit.GetParameter(1)"
        print fit.GetParameter(1)
        print "fit.GetParameter(2)"
        print fit.GetParameter(2)

    if (fit.GetParameter(3)<0): ##if [3]<0, I have to exchange [0],[1] min/max
        for i in [0,1]:
            print "CHANGE"
            print parametersUp[i],parametersDown[i]
            tmp = parametersUp[i]
            parametersUp[i] = parametersDown[i]
            parametersDown[i] = tmp
            print parametersUp[i],parametersDown[i]

    ## end
    for i in range(len(parameters)):
        print "i=,",i,"\t",parameters[i],"\t",parametersUp[i],"\t",parametersDown[i]
        fit.SetParameter(i,parameters[i])
        fitUp.SetParameter(i,parametersUp[i])
        fitDown.SetParameter(i,parametersDown[i])

    return fit,fitUp,fitDown



def doPlots(ped,fileNum,fileDen,drawOption=""):

    if drawOption=="":
        MC_num, data_num = getMCAndData(fileNum)
        MC_den, data_den = getMCAndData(fileDen)

        turnOnMC = doRatio(MC_num,MC_den,"b")
        turnOnData = doRatio(data_num,data_den,"b")
    else:
        drawOption["fileName"]=fileDen
        data_num,data_den =  makeHistos(**drawOption)
        drawOption["fileName"]=fileNum
        MC_num,MC_den =  makeHistos(**drawOption)

        turnOnMC = doRatio(MC_num,MC_den,"b")
        turnOnData = doRatio(data_num,data_den,"b")
        #do plot!
#    DataMC = doRatio(turnOnData,turnOnMC)

    #function = ROOT.TF1("turnonPt","1-(0.5-0.5*erf( (x-[0])/[1]))*([3])-[2] ",functionMin,functionMax)
    function = ROOT.TF1("turnonPt","1-(0.5-0.5*TMath::Erf( (x-[0])/[1]))*([3])-[2] ",functionMin,functionMax)
#    function = ROOT.TF1("turnonPt","(0.5+0.5*TMath::Erf( (x-[0])*(x-[0]>[5])/[1] + (x-[0])*(x-[0]<[5])/[2] + [5]*(1/[1]-1/[2])*(x-[0]<[5]) ))*[4]+[3] ",functionMin,functionMax)
    function.SetParameters(*parametersTurnOn)
#    function.SetParLimits(3,-1,2)
#    function.SetParLimits(4,-1,1)
    function.SetLineWidth(2)


    TurnOnMC = function.Clone("TurnOnMC")
    TurnOnData = function.Clone("TurnOnData")

    c1 = ROOT.TCanvas("c1","",1280,720)

    TurnOnMC,TurnOnMCUp,TurnOnMCDown = confidenceInterval(turnOnMC,TurnOnMC)

    turnOnMC.SetMaximum(maxTurnOn)
    turnOnMC.SetMinimum(minTurnOn)
    turnOnMC.GetXaxis().SetTitle(title)
    turnOnMC.GetYaxis().SetTitle("Efficiency")

    turnOnMC.Draw("AP")
    TurnOnMC.Draw("same")
    TurnOnMCUp.Draw("same")
    TurnOnMCDown.Draw("same")

    c1.SaveAs("turnOnMC_"+ped+".png")
    c1.SaveAs("turnOnMC_"+ped+".root")

    TurnOnData,TurnOnDataUp,TurnOnDataDown = confidenceInterval(turnOnData,TurnOnData)

    turnOnData.SetMaximum(maxTurnOn)
    turnOnData.SetMinimum(minTurnOn)
    turnOnData.GetXaxis().SetTitle(title)
    turnOnData.GetYaxis().SetTitle("Efficiency")

    turnOnData.Draw("AP")
    TurnOnData.Draw("same")
    TurnOnDataUp.Draw("same")
    TurnOnDataDown.Draw("same")

    c1.SaveAs("turnOnData_"+ped+".png")
    c1.SaveAs("turnOnData_"+ped+".root")

    print "Ratio do"
    ratio = DivideTGraph(turnOnData,turnOnMC)
    print "Ratio done"

    ratioFit=function.Clone("ratioFit")
    ratioFit.SetParameters(*parametersRatio)

    ratioFit,ratioFitUp,ratioFitDown = confidenceInterval(ratio,ratioFit)

    ratio.SetMaximum(maxRatio)
    ratio.SetMinimum(minRatio)

    ratio.SetTitle("Data/MC efficiency ratio")
    ratio.GetXaxis().SetTitle(title)
    ratio.GetYaxis().SetTitle("ratio")
    ratio.Draw("AP")
    ratioFit.Draw("same")
    ratioFitUp.Draw("same")
    ratioFitDown.Draw("same")

#    f.write(('TF1* %s = new TF1("%s","'%(ped,ped)           + str(ratioFit.GetExpFormula("P"))+'");\n'))
#    f.write(('TF1* %sUp = new TF1("%sUp","'%(ped,ped)       + str(ratioFitUp.GetExpFormula("P"))+'");\n'))
#    f.write(('TF1* %sDown = new TF1("%sDown","'%(ped,ped)   + str(ratioFitDown.GetExpFormula("P"))+'");\n'))

    f.write(('TF1* %s = new TF1("%s","'%(ped,ped)           + str(TurnOnMC.GetExpFormula("P"))+'");\n'))
    f.write(('TF1* %sUp = new TF1("%sUp","'%(ped,ped)       + str(TurnOnMCUp.GetExpFormula("P"))+'");\n'))
    f.write(('TF1* %sDown = new TF1("%sDown","'%(ped,ped)   + str(TurnOnMCDown.GetExpFormula("P"))+'");\n'))

#    print 'TF1 ratioFit = TF1("ratioFit","', ratioFit.GetExpFormula("P"),'",50,500)'
#    print 'TF1 ratioFitUp = TF1("ratioFitUp","', ratioFitUp.GetExpFormula("P"),'",50,500)'
#    print 'TF1 ratioFitDown = TF1("ratioFitDown","', ratioFitDown.GetExpFormula("P"),'",50,500)'

    c1.SaveAs("ratio_"+ped+".png")
    c1.SaveAs("ratio_"+ped+".root")

    colorMC = ROOT.kBlue
    colorData = ROOT.kRed
    turnOnMC.SetLineColor(colorMC)
    turnOnMC.SetMarkerColor(colorMC)
    turnOnMC.SetMarkerStyle(22)
    turnOnMC.SetMarkerSize(1.5)
    TurnOnMC.SetLineColor(colorMC)
    turnOnData.SetLineColor(colorData)
    turnOnData.SetMarkerColor(colorData)
    turnOnData.SetMarkerSize(1.5)
    turnOnData.SetMarkerStyle(23)
    TurnOnData.SetLineColor(colorData)

    turnOnData.SetTitle("Trigger efficiency")
    turnOnData.GetXaxis().SetTitle(title)
    turnOnData.GetYaxis().SetTitle("Efficiency")

    turnOnData.Draw("AP")
    TurnOnData.Draw("same")

    turnOnMC.Draw("P")
    TurnOnMC.Draw("same")

    leg = ROOT.TLegend(0.7,0.15,0.95,0.3);
    leg.AddEntry(turnOnMC,"MC","lp");
    leg.AddEntry(turnOnData,"Data","lp");
    leg.Draw();


    c1.SaveAs("both_"+ped+".png")
    c1.SaveAs("both_"+ped+".root")

    function.Delete()
    TurnOnMC.Delete()
    TurnOnMCDown.Delete()
    TurnOnMCUp.Delete()
    TurnOnData.Delete()
    TurnOnDataDown.Delete()
    TurnOnDataUp.Delete()
    ratioFit.Delete()


ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptFit(0)


minRatio    = 0.5
maxRatio    = 1.5

#fileData    = "/scratch/sdonato/VHbbRun2/V20/CMSSW_7_1_5/src/Xbb/env_turnOnMET90/ZvvHighPt_V20_SingleMuon.root"
fileData    = "/gpfs/ddn/srm/cms/store/user/arizzi/VHBBHeppyV20/SingleMuon/VHBB_HEPPY_V20_SingleMuon__Run2015D-16Dec2015-v1/160210_081323/0000/tree*.root"
fileMC      = "/scratch/sdonato/VHbbRun2/V20/CMSSW_7_1_5/src/Xbb/env_turnOnMET90/ZvvHighPt_V20_TT_TuneCUETP8M1_13TeV-powheg-pythia8.root"

preselection = "HLT_BIT_HLT_IsoMu18_v"

parametersTurnOn = (50,50,0,1,0)
parametersRatio = (105,45,0.01,1,0)
#parametersTurnOn = (50,50,50,0,1,0)
#parametersRatio = (105,45,45,0.01,1,0)

#################### L1 #########################

functionMin = 15
functionMax = 500
drawOption={
    "var"           :"Jet_pt[0]+Jet_pt[1]+Jet_pt[2]+Jet_pt[3]",
    "trigger"       :"ntrgObjects_hltQuadCentralJet45>=1",
    "preselection"  :preselection,
    "binning"       :(40,0,400)
}
ped         = "QuaJet_L1"
title       = "p^{T}_{1}+p^{T}_{2}+p^{T}_{3}"
doPlots(ped,fileMC,fileData,drawOption)

#################### CaloPt4 #########################

functionMin = 15
functionMax = 500
preselection = preselection + "&&"+drawOption["trigger"]
drawOption={
    "var"           :"Jet_pt[3]",
    "trigger"       :"ntrgObjects_hltQuadCentralJet45>=4",
    "binning"       :(40,0,120),
    "preselection"  :preselection,
}
ped         = "QuaJet_CaloPt4"
title       = "p^{T}_{4}"
doPlots(ped,fileMC,fileData,drawOption)

parametersTurnOn = (1.2,1.4,0.2,0.8)
parametersRatio = (1.2,1.4,0.2,0.8)
#parametersTurnOn = (1,0.2,0.2,0,1,0)
#parametersRatio = (1,0.2,0.2,0.01,1,0)

#################### CSV3 #########################

functionMin = 0
functionMax = 500
preselection = preselection + "&&"+drawOption["trigger"]
drawOption={
    "var"           :"-log(1-Jet_btagCSV[aJCidx[0]])",
    "trigger"       :"ntrgObjects_hltTripleCSV0p67>=3",
    "binning"       :(40,0,8),
    "preselection"  :preselection,
}
ped         = "QuaJet_LogCSV3"
title       = "-log(1-CSV_{3})"
doPlots(ped,fileMC,fileData,drawOption)

parametersTurnOn = (50,50,0,1,0)
parametersRatio = (105,45,0.01,1,0)
#parametersTurnOn = (50,50,50,0,1,0)
#parametersRatio = (105,45,45,0.01,1,0)

##################### PFPt4 ########################

functionMin = 15
functionMax = 500
preselection = preselection + "&&"+drawOption["trigger"]
drawOption={
    "var"           :"Jet_pt[3]",
    "trigger"       :"ntrgObjects_hltQuadPFCentralJetLooseID45>=4",
    "binning"       :(40,0,120),
    "preselection"  :preselection,
}
ped         = "QuaJet_PFPt4"
title       = "p^{T}_{4}"
doPlots(ped,fileMC,fileData,drawOption)

#############################################
#f.Close()
