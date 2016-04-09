import ROOT
import copy
from math import *
import array

ROOT.gROOT.LoadMacro("tdrstyleTrigger.C")
ROOT.setTDRStyle()

minTurnOn   = 0
maxTurnOn   = 1

minRatio    = 0.8
maxRatio    = 1.2

functionMin = -1E-6
functionMax = 1E-6

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

    print "Xs_den",Xs_den
    Xs_new   = [ Xs_den[i] for i in range( Ns_den)]
    print "Xs_new",Xs_new
    Ys_new   = [ Ys_num[i]/(Ys_den[i]+1E-7) for i in range( Ns_den)]
    EXLs_new = [ EXLs_den[i] for i in range( Ns_den)]
    EXHs_new = [ EXHs_den[i] for i in range( Ns_den)]
    [ EYLs_num[i] for i in range( Ns_den)]
    [ ((EYLs_num[i]/(Ys_num[i]+1E-7))**2) for i in range( Ns_den)]
    [ Ys_new[i]*sqrt((EYLs_num[i]/(Ys_num[i]+1E-7))**2) for i in range( Ns_den)]
    EYLs_new = [ Ys_new[i]*sqrt((EYLs_num[i]/(Ys_num[i]+1E-7))**2+(EYHs_den[i]/(Ys_den[i]+1E-7))**2) for i in range( Ns_den)]
    EYHs_new = [ Ys_new[i]*sqrt((EYHs_num[i]/(Ys_num[i]+1E-7))**2+(EYLs_den[i]/(Ys_den[i]+1E-7))**2) for i in range( Ns_den)]

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

    print "fileName: ",fileName
    print "MC(integral,min,max,bins): ",MC.Integral(),MC.GetXaxis().GetXmin(),MC.GetXaxis().GetXmax(),MC.GetXaxis().GetNbins()
    print "data(integral,min,max,bins): ",data.Integral(),data.GetXaxis().GetXmin(),data.GetXaxis().GetXmax(),data.GetXaxis().GetNbins()

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
        for i in range(num.GetNbinsX()+2):print num.GetBinLowEdge(i),
        print ""
        for i in range(den.GetNbinsX()+2): print den.GetBinLowEdge(i),
        print ""
        for i in range(num.GetNbinsX()+2):print num.GetBinContent(i)/(1E-5+den.GetBinContent(i)),
        print ""

        for i in range(den.GetNbinsX()+2):
            if den.GetBinContent(i)<=0:
                den.SetBinContent(i,1.E-5)
                den.SetBinError(i,10)
        for i in range(num.GetNbinsX()+2):
            if num.GetBinContent(i)<=0:
                num.SetBinContent(i,1.E-7)
                num.SetBinError(i,10)
        for i in range(den.GetNbinsX()+2):
            if num.GetBinContent(i)>den.GetBinContent(i):
                print "WARNING!"
                print num.GetBinContent(i),den.GetBinContent(i)
                num.SetBinContent(i,den.GetBinContent(i))
#            num.SetBinContent(i,num.GetBinContent(i))
#            den.SetBinContent(i,den.GetBinContent(i))

        for i in range(num.GetNbinsX()):print num.GetBinContent(i)/(1E-5+den.GetBinContent(i)),
        print ""

        mratio.Divide(num,den,"cl=0.683 b(1,1) mode")
        print "End ratio. bins:",mratio.GetN()," num:",num.GetNbinsX()," den:",den.GetNbinsX()
        return mratio

def confidenceInterval(graph, function):
    print "Launching confidenceInterval"
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
    parameters = [0]*4
    for i in range(4):
        parameters[i] = fit.GetParameter(i)

    parametersUp = parameters[:]
    parametersDown = parameters[:]

    looseRange=10.
    tightRange=10.

    print "Up/down fit"

    ## FixParameters
    for i in range(4):
        fit.ReleaseParameter(i)
#        if i in [0]: #  x0 can go down
#            pass
#        elif i in [3]: # global efficiency can go up
#            pass
        if i in [0,2]: #  x0 can go down
            pass
        else: # fix the other parameters
            fit.FixParameter( i, parameters[i] )
    fitResult = graph.Fit(fit,"SEV0","",fit.GetXmin(),fit.GetXmax())
    ## Up
    for i in range(4):
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
    for i in range(4):
        print "i=,",i,"\t",parameters[i],"\t",parametersUp[i],"\t",parametersDown[i]
        fit.SetParameter(i,parameters[i])
        fitUp.SetParameter(i,parametersUp[i])
        fitDown.SetParameter(i,parametersDown[i])

    print "Ending confidenceInterval"
    return fit,fitUp,fitDown



def doPlots(ped,fileNum,fileDen):

    MC_num, data_num = getMCAndData(fileNum)
    MC_den, data_den = getMCAndData(fileDen)

    turnOnMC = doRatio(MC_num,MC_den,"b")
    turnOnData = doRatio(data_num,data_den,"b")

#    DataMC = doRatio(turnOnData,turnOnMC)

    #function = ROOT.TF1("turnonPt","1-(0.5-0.5*erf( (x-[0])/[1]))*([3])-[2] ",functionMin,functionMax)
    function = ROOT.TF1("turnonPt","1-(0.5-0.5*TMath::Erf( (x-[0])/[1]))*([3])-[2] ",functionMin,functionMax)
    function.SetParameters(105,45,0.01,1)
    function.SetParLimits(0,0,200)
    function.SetParLimits(1,0,100)
    function.SetLineWidth(2)


    TurnOnMC = function.Clone("TurnOnMC")
    TurnOnData = function.Clone("TurnOnData")

    c1 = ROOT.TCanvas("c1","",1280,720)

    TurnOnMC,TurnOnMCUp,TurnOnMCDown = confidenceInterval(turnOnMC,TurnOnMC)

    turnOnMC.SetMaximum(maxTurnOn)
    turnOnMC.SetMinimum(minTurnOn)
    turnOnMC.GetXaxis().SetTitle(title)
    turnOnMC.GetYaxis().SetTitle("Efficiency")


    turnOnMC.GetXaxis().SetRangeUser(functionMin,functionMax)
    turnOnMC.Draw("AP")
    TurnOnMC.Draw("same")
#    TurnOnMCUp.Draw("same")
#    TurnOnMCDown.Draw("same")

    c1.SaveAs("turnOnMC_"+ped+".png")
    c1.SaveAs("turnOnMC_"+ped+".root")

    TurnOnData,TurnOnDataUp,TurnOnDataDown = confidenceInterval(turnOnData,TurnOnData)

    turnOnData.SetMaximum(maxTurnOn)
    turnOnData.SetMinimum(minTurnOn)
    turnOnData.GetXaxis().SetTitle(title)
    turnOnData.GetYaxis().SetTitle("Efficiency")

    turnOnData.GetXaxis().SetRangeUser(functionMin,functionMax)
    turnOnData.Draw("AP")
    TurnOnData.Draw("same")
#    TurnOnDataUp.Draw("same")
#    TurnOnDataDown.Draw("same")

    c1.SaveAs("turnOnData_"+ped+".png")
    c1.SaveAs("turnOnData_"+ped+".root")

    print "Ratio do"
    ratio = DivideTGraph(turnOnData,turnOnMC)
    print "Ratio done"

    ratioFit=function.Clone("ratioFit")
    ratioFit.SetParLimits(0,-1,1)
    ratioFit.SetParLimits(1,-100,200)
    ratioFit.SetParLimits(2,-1,1)
    ratioFit.SetParLimits(3,1,50)
    ratioFit.SetParameters(-0.01,75,0.005,7)

    ratioFit,ratioFitUp,ratioFitDown = confidenceInterval(ratio,ratioFit)

    ratio.SetMaximum(maxRatio)
    ratio.SetMinimum(minRatio)

    ratio.SetTitle("Data/MC efficiency ratio")
    ratio.GetXaxis().SetTitle(title)
    ratio.GetYaxis().SetTitle("Data/MC")
    ratio.Draw("AP")
    ratio.GetXaxis().SetRangeUser(functionMin,functionMax)
    ratioFit.Draw("same")
    ratioFitUp.Draw("same")
    ratioFitDown.Draw("same")

    print 'TF1 ratioFit = TF1("ratioFit","', ratioFit.GetExpFormula("P"),'",50,500)'
    print 'TF1 ratioFitUp = TF1("ratioFitUp","', ratioFitUp.GetExpFormula("P"),'",50,500)'
    print 'TF1 ratioFitDown = TF1("ratioFitDown","', ratioFitDown.GetExpFormula("P"),'",50,500)'

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

    turnOnData.GetXaxis().SetRangeUser(functionMin,functionMax)
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
################################

#    turnOnData.SetMaximum(maxTurnOn)
#    turnOnData.SetMinimum(minTurnOn)
#    turnOnData.GetYaxis().SetTitle("Efficiency")
#    turnOnData.Fit(TurnOnData,"WW")
#    turnOnData.Fit(TurnOnData,"")
#    for i in [1,2]:
#        TurnOnData.FixParameter( i, TurnOnData.GetParameter(i) )
#
#    turnOnData.Fit(TurnOnData,"E")
#    turnOnData.Draw("AP")

#    TurnOnDataUp = TurnOnData.Clone("TurnOnDataUp")
#    TurnOnDataUp.SetLineColor(ROOT.kBlack)
#    TurnOnDataDown = TurnOnData.Clone("TurnOnDataDown")
#    TurnOnDataDown.SetLineColor(ROOT.kBlue)
#    for i in [0,1,2,3]:
#        if i in [2,3]:
#            TurnOnDataUp.SetParameter(i,TurnOnDataUp.GetParameter(i) + TurnOnDataUp.GetParError(i))
#            TurnOnDataDown.SetParameter(i,TurnOnDataDown.GetParameter(i) - TurnOnDataDown.GetParError(i))
#        else:
#            TurnOnDataUp.SetParameter(i,TurnOnDataUp.GetParameter(i) - TurnOnDataUp.GetParError(i))
#            TurnOnDataDown.SetParameter(i,TurnOnDataDown.GetParameter(i) + TurnOnDataDown.GetParError(i))
#
#    TurnOnData.Draw("same")
#    TurnOnDataUp.Draw("same")
#    TurnOnDataDown.Draw("same")

#    c1.SaveAs("turnOnData_"+ped+".png")
#    c1.SaveAs("turnOnData_"+ped+".C")

################################


#    DataMC.SetMaximum(maxRatio)
#    DataMC.SetMinimum(minRatio)
#    DataMC.GetYaxis().SetTitle("Scale factor (data/MC)")
#    DataMC.Draw()
#    DataMC.Fit(function)
#    TurnOnDataUp = function.Clone("TurnOnDataUp")
#    TurnOnDataUp.SetLineColor(ROOT.kBlack)
#    TurnOnDataDown = function.Clone("TurnOnDataDown")
#    TurnOnDataDown.SetLineColor(ROOT.kBlue)
#    for i in range(4):
#        if i in [2,3]:
#            TurnOnDataUp.SetParameter(i,TurnOnDataUp.GetParameter(i) + TurnOnDataUp.GetParError(i))
#            TurnOnDataDown.SetParameter(i,TurnOnDataDown.GetParameter(i) - TurnOnDataDown.GetParError(i))
#        else:
#            TurnOnDataUp.SetParameter(i,TurnOnDataUp.GetParameter(i) - TurnOnDataUp.GetParError(i))
#            TurnOnDataDown.SetParameter(i,TurnOnDataDown.GetParameter(i) + TurnOnDataDown.GetParError(i))


#    for i in range(4):
#        print "function.GetParameter(i)",function.GetParameter(i)
#        print "TurnOnDataUp.GetParameter(i)",TurnOnDataUp.GetParameter(i)
#        print "TurnOnDataDown.GetParameter(i)",TurnOnDataDown.GetParameter(i)

#    print "TurnOnDataDown: ",TurnOnDataDown.GetExpFormula("P")
#    print "TurnOnDataUp: ",TurnOnDataUp.GetExpFormula("P")
#    print "function: ",function.GetExpFormula("P")
#
#
#    function.Draw("same")
#    TurnOnDataUp.Draw("same")
#    TurnOnDataDown.Draw("l,same")

#    c1.SaveAs("DataMC_"+ped+".png")
#    c1.SaveAs("DataMC_"+ped+".C")

ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptFit(0)

#fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnEleNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnEleDen_minMETMHT_125.root"
#fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0_TurnOn_withQCD/root/TurnOnEleNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0_TurnOn_withQCD/root/TurnOnEleDen_minMETMHT_125.root"
#ped="ele"
#doPlots(ped,fileNum,fileDen)

##fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnMuNum_minMETMHT_125.root"
##fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnMuDen_minMETMHT_125.root"
#fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0_TurnOn_withQCD/root/TurnOnMuNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0_TurnOn_withQCD/root/TurnOnMuDen_minMETMHT_125.root"

##############################################

#fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnMuNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnMuDen_minMETMHT_125.root"
#ped="mu"
#doPlots(ped,fileNum,fileDen)

#fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnEleNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnEleDen_minMETMHT_125.root"
#ped="ele"
#doPlots(ped,fileNum,fileDen)

#fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnTTMuNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnTTMuDen_minMETMHT_125.root"
#ped="mu_TT"
#doPlots(ped,fileNum,fileDen)

#fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnTTEleNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnTTEleDen_minMETMHT_125.root"
#ped="ele_TT"
#doPlots(ped,fileNum,fileDen)

######################

#fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDMuNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDMuDen_minMETMHT_125.root"
#ped="mu_QCD"
#doPlots(ped,fileNum,fileDen)

#fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDEleNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDEleDen_minMETMHT_125.root"
#ped="ele_QCD"
#doPlots(ped,fileNum,fileDen)

#fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDTTMuNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDTTMuDen_minMETMHT_125.root"
#ped="mu_TT_QCD"
#doPlots(ped,fileNum,fileDen)

#fileNum = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDTTEleNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDTTEleDen_minMETMHT_125.root"
#ped="ele_TT_QCD"
#doPlots(ped,fileNum,fileDen)


###############################

#fileNum = "/scratch/sdonato/VHbbRun2/V14_forPreApproval/triggerMET/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnEleNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14_forPreApproval/triggerMET/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnEleDen_minMETMHT_125.root"
#ped="ele_std"
#doPlots(ped,fileNum,fileDen)

#fileNum = "/scratch/sdonato/VHbbRun2/V14_forPreApproval/triggerMET/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnMuNum_minMETMHT_125.root"
#fileDen = "/scratch/sdonato/VHbbRun2/V14_forPreApproval/triggerMET/CMSSW_7_4_7_patch1/src/Xbb/Stacks_expertAllnominal_v0.0.0/root/TurnOnMuDen_minMETMHT_125.root"
#ped="mu_std"
#doPlots(ped,fileNum,fileDen)

###############################
minRatio    = 0.8
maxRatio    = 1.2

minTurnOn   = 0.25
maxTurnOn   = 1.05

functionMin = 99
functionMax = 500

fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDTTMuNum_minMETMHT_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDTTMuDen_minMETMHT_125.root"
ped="mu_TT"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)


fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDTTEleNum_minMETMHT_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDTTEleDen_minMETMHT_125.root"
ped="ele_TT"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)

minRatio    = 0.8
maxRatio    = 1.2

minTurnOn   = 0.
maxTurnOn   = 1.

functionMin = 0
functionMax = 8

fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDTTEleNum_maxLogCSVTurnOn_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDTTEleDen_maxLogCSVTurnOn_125.root"
ped="ele_TT_LogCSV"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)


fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDTTMuNum_maxLogCSVTurnOn_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDTTMuDen_maxLogCSVTurnOn_125.root"
ped="mu_TT_LogCSV"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)


functionMin = 0
functionMax = 1


fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDTTEleNum_maxCSVTurnOn_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDTTEleDen_maxCSVTurnOn_125.root"
ped="ele_TT_CSV"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)


fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDTTMuNum_maxCSVTurnOn_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDTTMuDen_maxCSVTurnOn_125.root"
ped="mu_TT_CSV"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)

####################################################################


minRatio    = 0.8
maxRatio    = 1.2

minTurnOn   = 0.25
maxTurnOn   = 1.05

functionMin = 99
functionMax = 500

fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDMuNum_minMETMHT_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDMuDen_minMETMHT_125.root"
ped="mu_std"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)


fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDEleNum_minMETMHT_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnQCDEleDen_minMETMHT_125.root"
ped="ele_std"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)

minRatio    = 0.8
maxRatio    = 1.2

minTurnOn   = 0.
maxTurnOn   = 1.

functionMin = 0
functionMax = 8

fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDEleNum_maxLogCSVTurnOn_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDEleDen_maxLogCSVTurnOn_125.root"
ped="ele_std_LogCSV"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)


fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDMuNum_maxLogCSVTurnOn_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDMuDen_maxLogCSVTurnOn_125.root"
ped="mu_std_LogCSV"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)


functionMin = 0
functionMax = 1


fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDEleNum_maxCSVTurnOn_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDEleDen_maxCSVTurnOn_125.root"
ped="ele_std_CSV"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)


fileNum = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDMuNum_maxCSVTurnOn_125.root"
fileDen = "../../../Stacks_expertAllnominal_v0.0.0/root/TurnOnCSVQCDMuDen_maxCSVTurnOn_125.root"
ped="mu_std_CSV"
title = getTitle(fileNum)
doPlots(ped,fileNum,fileDen)

