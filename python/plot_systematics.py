#!/usr/bin/env python
import ROOT 
ROOT.gROOT.SetBatch(True)
from ROOT import TFile
from optparse import OptionParser
import sys
from myutils import BetterConfigParser, TdrStyles, getRatio


argv = sys.argv
parser = OptionParser()
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
(opts, args) = parser.parse_args(argv)
config = BetterConfigParser()
config.read(opts.config)


#---------- yes, this is not in the config yet---------
mode = 'BDT'
xMin=-1
xMax=1
masses = ['125']
#Abins = ['HighPt','LowPt']
Abins = ['HighPt']
#Abins = ['LowPt']
#channels= ['Zee','Zmm']
channels= ['Zmm']
#------------------------------------------------------
#---------- Mjj ---------------------------------------
#mode = 'Mjj'
#xMin=0
#xMax=255
#masses = ['125']
#Abins = ['highPt','lowPt','medPt']
#channels= ['Zee','Zmm']
#------------------------------------------------------

path = config.get('Directories','limits')
outpath = config.get('Directories','plotpath')

setup = eval(config.get('LimitGeneral','setup'))
Dict = eval(config.get('LimitGeneral','Dict'))
MCs = [Dict[s] for s in setup]

sys_BDT= eval(config.get('LimitGeneral','sys_BDT'))
systematicsnaming = eval(config.get('LimitGeneral','systematicsnaming'))
systs=[systematicsnaming[s] for s in sys_BDT]
sys_weight = eval(config.get('LimitGeneral','weightF_sys'))

for sw in  sys_weight: systs.append(systematicsnaming[sw])

#What are those ?
#if eval(config.get('LimitGeneral','weightF_sys')): systs.append('UEPS')

def myText(txt="CMS Preliminary",ndcX=0,ndcY=0,size=0.8):
    ROOT.gPad.Update()
    text = ROOT.TLatex()
    text.SetNDC()
    text.SetTextColor(ROOT.kBlack)
    text.SetTextSize(text.GetTextSize()*size)
    text.DrawLatex(ndcX,ndcY,txt)
    return text


#for mass in ['110','115','120','125','130','135']:
for mass in masses:
    for Abin in Abins:
        for channel in channels:

            if mode == 'BDT':
                #input = TFile.Open(path+'/vhbb_TH_BDT_M'+mass+'_'+channel+Abin+'_8TeV.root','read')
                #input = TFile.Open()

                #input = TFile.Open(path+'vhbb_TH_ZmmLowPt_13TeV.root','read')
                #input = TFile.Open(path+'vhbb_TH_ZmmHighPt_13TeV.root','read')
                input = TFile.Open(path+'vhbb_TH_ZmmBDT_SCAN_NTrees_100_nEventsMin_400_Zmm_highVpt.root','read')
            if mode == 'Mjj':
                input = TFile.Open(path+'/vhbb_TH_Mjj_'+Abin+'_M'+mass+'_'+channel+'.root','read')

            print 'The MCs are'
            for MC in MCs:
                print MC
                print 'The systs are'
                for syst in systs:
                    print syst
                #['CMS_res_j','CMS_scale_j','CMS_eff_b','CMS_fake_b_8TeV','UEPS']:
                #for syst in ['CMS_vhbb_stats_']:


                    TdrStyles.tdrStyle()

                    c = ROOT.TCanvas('','', 600, 600)
                    c.SetFillStyle(4000)
                    c.SetFrameFillStyle(1000)
                    c.SetFrameFillColor(0)
                    oben = ROOT.TPad('oben','oben',0,0.3 ,1.0,1.0)
                    oben.SetBottomMargin(0)
                    oben.SetFillStyle(4000)
                    oben.SetFrameFillStyle(1000)
                    oben.SetFrameFillColor(0)
                    unten = ROOT.TPad('unten','unten',0,0.0,1.0,0.3)
                    unten.SetTopMargin(0.)
                    unten.SetBottomMargin(0.35)
                    unten.SetFillStyle(4000)
                    unten.SetFrameFillStyle(1000)
                    unten.SetFrameFillColor(0)
                    oben.Draw()
                    unten.Draw()
                    oben.cd()

                    ROOT.gPad.SetTicks(1,1)


                    #input.cd("Vpt1")
                    input.cd("Vpt2")
                    print 'Ntotal is', MC
                    print 'Utotal is', MC+syst+'Up'
                    print 'Dtotal is', MC+syst+'Down'
                    Ntotal=ROOT.gDirectory.Get(MC)
                    Utotal=ROOT.gDirectory.Get(MC+syst+'Up')
                    #Utotal=input.Get(MC+syst+MC+'_'+channel+'Up')
                    Dtotal=ROOT.gDirectory.Get(MC+syst+'Down')
                    #Dtotal=input.Get(MC+syst+MC+'_'+channel+'Down')
                    l = ROOT.TLegend(0.17, 0.8, 0.37, 0.65)
                    
                    l.SetLineWidth(2)
                    l.SetBorderSize(0)
                    l.SetFillColor(0)
                    l.SetFillStyle(4000)
                    l.SetTextFont(62)
                    l.SetTextSize(0.035)

                    
                    l.AddEntry(Ntotal,'nominal','PL')
                    l.AddEntry(Utotal,'up','PL')
                    l.AddEntry(Dtotal,'down','PL')
                    Ntotal.GetYaxis().SetRangeUser(0,1.5*Ntotal.GetBinContent(Ntotal.GetMaximumBin()))
                    Ntotal.SetMarkerStyle(8)
                    Ntotal.SetLineColor(1)
                    Ntotal.SetStats(0)
                    Ntotal.SetTitle(MC +' '+syst)
                    Ntotal.Draw("P0")
                    Ntotal.Draw("same")
                    Utotal.SetLineColor(4)    
                    Utotal.SetLineStyle(4)
                    Utotal.SetLineWidth(2)        
                    Utotal.Draw("same hist")
                    Dtotal.SetLineColor(2)
                    Dtotal.SetLineStyle(3)
                    Dtotal.SetLineWidth(2)  
                    Dtotal.Draw("same hist")
                    l.SetFillColor(0)
                    l.SetBorderSize(0)
                    l.Draw()
                    
                    title=myText('Shape Systematic %s in %s'%(syst,MC),0.17,0.85)
                    
                    print 'Shape Systematic %s in %s'%(syst,MC)
                    print 'Up:     \t%s'%Utotal.Integral()
                    print 'Nominal:\t%s'%Ntotal.Integral()
                    print 'Down:   \t%s'%Dtotal.Integral()
                    
                    unten.cd()
                    ROOT.gPad.SetTicks(1,1)

                    ratioU, errorU  = getRatio(Utotal,Ntotal,xMin,xMax)
                    ratioD, errorD  = getRatio(Dtotal,Ntotal,xMin,xMax)

                    ksScoreU = Ntotal.KolmogorovTest( Utotal )
                    chiScoreU = Ntotal.Chi2Test( Utotal , "WWCHI2/NDF")
                    ksScoreD = Ntotal.KolmogorovTest( Dtotal )
                    chiScoreD = Ntotal.Chi2Test( Dtotal , "WWCHI2/NDF")


                    ratioU.SetStats(0)
                    ratioU.GetYaxis().SetRangeUser(0.5,1.5)
                    ratioU.GetYaxis().SetNdivisions(502,0)
                    ratioD.SetStats(0)
                    ratioD.GetYaxis().SetRangeUser(0.5,1.5)
                    ratioD.GetYaxis().SetNdivisions(502,0)
                    ratioD.GetYaxis().SetLabelSize(0.05)
                    ratioD.SetLineColor(2)
                    ratioD.SetLineStyle(3)
                    ratioD.SetLineWidth(2)
                    ratioU.SetLineColor(4)
                    ratioU.SetLineStyle(4)
                    ratioU.SetLineWidth(2)

                    fitRatioU = ratioU.Fit("pol2","S")
                    ratioU.GetFunction("pol2").SetLineColor(4)
                    fitRatioD = ratioD.Fit("pol2","S")
                    ratioU.Draw("APSAME")
                    ratioD.GetXaxis().SetTitle('BDT Output')
                    ratioD.GetYaxis().SetTitle('Ratio')
                    ratioD.GetYaxis().SetTitleSize(0.1)
                    ratioD.GetYaxis().SetTitleOffset(0.2)
                    fitRatioU.Draw("SAME")
                    fitRatioD.Draw("SAME")

                    ratioD.Draw("SAME")

                    #name = outpath+Abin+'_M'+mass+'_'+channel+'_'+MC+syst+'.png'
                    #c.Print(name)
                    name = outpath+'systPlot_'+Abin+'_M'+mass+'_'+channel+'_'+MC+syst+'.pdf'
                    c.Print(name)
                    c.Print(name.replace('.pdf','.png'))


            input.Close()
