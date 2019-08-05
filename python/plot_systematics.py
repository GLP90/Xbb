#!/usr/bin/env python
import ROOT 
ROOT.gROOT.SetBatch(True)
from ROOT import TFile
from optparse import OptionParser
import sys
from myutils import BetterConfigParser, TdrStyles, getRatio
import os

argv = sys.argv
parser = OptionParser()
parser.add_option("-C", "--config", dest="config", default=[], action="append", help="configuration file")
(opts, args) = parser.parse_args(argv)
print(opts.config)
config = BetterConfigParser()
config.read(opts.config)


#---------- yes, this is not in the config yet---------
mode = 'BDT'
xMin=-1
xMax=1
masses = ['125']
#channels = ['Zee_CRZb_incl_highpt','Zuu_CRZb_incl_highpt','Zee_CRZb_incl_lowpt','Zuu_CRZb_incl_lowpt','Zuu_CRttbar_highpt','Zee_CRttbar_highpt','Zuu_CRttbar_lowpt','Zee_CRttbar_lowpt','ZeeBDT_lowpt','ZeeBDT_highpt','ZuuBDT_highpt']

#channels = ['ZeeMassVV_highpt','ZeeMass_highpt']
#vhbb_TH_ZuuMass_highpt.root
#channels = ['ZuuMass_highpt']

#Test and test complementary
#channels = ['ZeeBDT_lowpt', 'ZuuBDT_highpt']
#channels = ['Zuu_CRZlight_lowpt','Zuu_CRZlight_highpt','Zee_CRZlight_lowpt','Zee_CRZlight_highpt','Zuu_CRZb_highpt','Zuu_CRZb_lowpt','Zee_CRZb_highpt','Zee_CRZb_lowpt','Zee_CRttbar_highpt','Zee_CRttbar_lowpt','Zuu_CRttbar_highpt','Zuu_CRttbar_lowpt','ZeeBDT_highpt','ZuuBDT_lowpt']
#channels = ['Wlm_SR_HighPt']
#channels = ['Wle_SR_HighPt']
#channels = ['Znn_13TeV_Signal']

#All
#channels = ['Zuu_CRZlight_lowpt','Zuu_CRZlight_highpt','Zee_CRZlight_lowpt','Zee_CRZlight_highpt','Zuu_CRZb_highpt','Zuu_CRZb_lowpt','Zee_CRZb_highpt','Zee_CRZb_lowpt','Zee_CRttbar_highpt','Zee_CRttbar_lowpt','Zuu_CRttbar_highpt','Zuu_CRttbar_lowpt','ZeeBDT_lowpt','ZeeBDT_highpt','ZuuBDT_lowpt','ZuuBDT_highpt']

#channels = ['ZeeBDT_lowpt']
#channels = ['Zee_CRZlight_lowpt']
#channels = ['Zuu_CRZlight_lowpt']
#Abins = ['HighPt','LowPt']
#Abins = ['HighPt']
#Abins = ['LowPt']
#channels= ['ZeeBDT_lowpt']
#channels= ['ZllBDT_lowpt']
#channels= ['ZllBDT_highpt']
#channels = ['ZeeBDT_lowpt','ZeeBDT_highpt','ZuuBDT_lowpt','ZuuBDT_highpt']
#channels = ['ZeeBDT_lowpt','ZeeBDT_highpt','ZuuBDT_lowpt','ZuuBDT_highpt']
#channels = ['Zuu_CRZlight_lowpt','Zee_CRZlight_lowpt','Zuu_CRZlight_highpt','Zee_CRZlight_highpt','Zee_CRZb_incl_highpt','Zuu_CRZb_incl_highpt','Zee_CRZb_incl_lowpt','Zuu_CRZb_incl_lowpt','Zuu_CRttbar_highpt','Zee_CRttbar_highpt','Zuu_CRttbar_lowpt','Zee_CRttbar_lowpt','ZeeBDT_lowpt','ZeeBDT_highpt','ZuuBDT_lowpt','ZuuBDT_highpt']
#channels = ['Zee_CRZb_incl_highpt','Zuu_CRZb_incl_highpt','Zee_CRZb_incl_lowpt','Zuu_CRZb_incl_lowpt','Zuu_CRttbar_highpt','Zee_CRttbar_highpt','Zuu_CRttbar_lowpt','Zee_CRttbar_lowpt','ZeeBDT_lowpt','ZeeBDT_highpt','ZuuBDT_lowpt','ZuuBDT_highpt']
#channels = ['Zee_CRZb_incl_highpt','Zuu_CRZb_incl_highpt','Zee_CRZb_incl_lowpt','Zuu_CRZb_incl_lowpt','Zuu_CRttbar_highpt','Zee_CRttbar_highpt','Zuu_CRttbar_lowpt','Zee_CRttbar_lowpt','ZeeBDT_lowpt','ZeeBDT_highpt','ZuuBDT_highpt']
#channels = ['ZeeBDT_highpt']
#channels = ['Zee_CRZlight_highpt']
#channels = ['Zee_CRZlight_lowpt']
#path_= '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_8_1_0/src/HiggsAnalysis/CombinedLimit/Nano2016/logs_Zvv2016Nano_V4_rundc_v21_Limits'

#path_= '/mnt/t3nfs01/data01/shome/gaperrin/VHbb2018/CMSSW_10_1_0/src/Xbb/python/logs_Wlv2016_v2/rundc_BDT0p5Cut_v20/Limits'
#path_= '/work/gaperrin/VHbb2018/CMSSW_10_1_0/src/Xbb/python/logs_Wlv2016_v2/rundc-boost-mva-v9/Limits'
#path_= '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_8_1_0/src/HiggsAnalysis/CombinedLimit/BOOST_Studies/Wlv/BOOST_final/BOODT_ovb'
#path_= '/work/gaperrin/VHbb2018/CMSSW_10_1_0/src/Xbb/python/logs_Wlv2016_v2/rundc_resolved_ovr_110729_v5/Limits'
#path_= '/work/gaperrin/VHbb2018/CMSSW_10_1_0/src/Xbb/python/logs_Wlv2016_v2/rundc_resolved_ovr_110729_v5/Limits'
#path_= '/work/gaperrin/VHbb2018/CMSSW_10_1_0/src/Xbb/python/logs_Wlv2016_v2/rundc_resolved_ovr_110729_v7/Limits'
#path_= '/work/gaperrin/VHbb2018/CMSSW_10_1_0/src/Xbb/python/logs_Wlv2016_v2/rundc_resolved_ovr_110729_v8/Limits'
#path_= '/work/gaperrin/VHbb2018/CMSSW_10_1_0/src/Xbb/python/logs_Wlv2016_v2/rundc_resolved_ovr_110729_v10/Limits'
#channels = ['Wlm_SR_HighPt_ovRESOLVED']

path_='/work/gaperrin/VHbb2018/CMSSW_10_1_0/src/Xbb/python/logs_Wlv2016_v2/rundc_JMR_var/Limits'
channels = ['vhbb_DC_TH_Sigu_BOOST']


#BOOST
channels = ['Sigu_BOOST']

#channels = ['Sigu_BOOST','Sige_BOOST','Wlm_Wlfv11_BOOST','Wle_Wlfv11_BOOST','Wle_Whf_BOOST','Wlm_Whf_BOOST','Wle_tt_BOOST','Wlm_tt_BOOST']


       

#------------------------------------------------------
#---------- Mjj ---------------------------------------
#mode = 'Mjj'
#xMin=0
#xMax=255
#masses = ['125']
#Abins = ['highPt','lowPt','medPt']
#channels= ['Zee','Zmm']
#------------------------------------------------------

#path = config.get('Directories','limits')
#outpath = config.get('Directories','plotpath')
outpath= path_.replace("Limits","plot_sys/")

if not os.path.exists(outpath):
  os.makedirs(outpath)

setup = eval(config.get('LimitGeneral','setup'))
Dict = eval(config.get('LimitGeneral','Dict'))
#MCs = [Dict[s] for s in setup]
#for test 
MCs = ['WH_hbb', 'TT']

sys_BDT= eval(config.get('LimitGeneral','sys_BDT'))
#sys_BDT= ['CUETP8M1']+eval(config.get('LimitGeneral','sys_BDT'))
#systematicsnaming = eval(config.get('LimitGeneral','systematicsnaming'))
#systematicsnaming = eval(config.get('LimitGeneral','systematicsnaming_HighPt'))
#systematicsnaming = eval(config.get('LimitGeneral','systematicsnaming_LowPt'))
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
    for channel in channels:

	if not os.path.exists(outpath+channel):
	  os.makedirs(outpath+channel)
        if mode == 'BDT':
            #input = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/SCAHINGDC_v5_CSV_6/'
            #input_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v25/MSCACHINGSPLIT_eval_v8_sigPS_All_rmvbr_VH_7/Limits//'
            #input_ = '/mnt/t3nfs01/data01/shome/vlohanes/CMSSW_10_1_0/src/Xbb/python/logs_Zll2016Nano_V4/rundc_fixednoPU-v3/Limits'

            input_ = '%s/vhbb_TH_%s.root'%(path_,channel)
            print 'input_ is', input_



	    input_ = '%s/vhbb_TH_%s.root'%(path_,channel)
            print 'input_ is', input_



            #'ZeeMass_lowpt':'ZeeMass_lowpt',if not 'ZeeBDT_lowpt' in input_: continue
            #if not ('ZeeMassVV_highpt' in input_ or 'ZeeMass_highpt' in input_): continue
            #if not ('ZuuMassVV_highpt' in input_ or 'ZuuMass_highpt' in input_): continue

            input = TFile.Open(input_,'read')
            print 'open', input
        if mode == 'Mjj':
            input = TFile.Open(path+'/vhbb_TH_Mjj_'+Abin+'_M'+mass+'_'+channel+'.root','read')
            print 'open', path+'/vhbb_TH_Mjj_'+Abin+'_M'+mass+'_'+channel+'.root'

        print 'input:', input
        print 'The MCs are', MCs
        for MC in MCs:
            #if not 'Top' in MC: continue
            print MC
            print 'The systs are'
            print systs
            for syst in systs:
                if '_m_' in syst and  ('Zee' in input_ or 'Wle' in input_): continue
                if '_e_' in syst and  ('Zuu' in input_ or 'Wlm' in input_): continue
                #if not 'EWK' in syst: continue
                #if not '_m_' in syst and not '_e_' in syst: continue
                #print syst
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
                #input.cd("Vpt2")
                dir_ = ''
                #dir_list = ['ZuuBDT_lowpt','ZuuBDT_highpt','ZeeBDT_lowpt','ZeeBDT_highpt']
                #dir_list = ['ZuuBDT_lowpt','ZuuBDT_highpt','ZeeBDT_lowpt','ZeeBDT_highpt']
                #dir_list = ['Zuu_CRZlight_lowpt']
                dir_list = channels
                #print 'dir_list is', dir_list
                for s in dir_list:
                    if s in input_: dir_ = s
                    print 's is', s
                if dir_ == '':
                    print('@ERROR: dir not found. Aborting')
                    sys.exit()
                #input.cd("ZeeBDT_lowpt")
                print 'dir_ is', dir_
                print 'channel is', channel
                print 'the list of channels is'
                #ROOT.gDirectory.GetListOfKeys().ls()
                input.cd(dir_)
                #skip _eff sys if not corresponding dc region

                if ('Sigu' in dir_ or 'Wlm' in dir_) and '_eff_e' in syst: continue
                if ('Sige' in dir_ or 'Wle' in dir_)and '_eff_m' in syst: continue
                #input.cd("ZllBDT_highpt")
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


                #l.AddEntry(Ntotal,'nominal','PL')
                #l.AddEntry(Utotal,'up','PL')
                #l.AddEntry(Dtotal,'down','PL')
                l.AddEntry(Ntotal,'nominal(%s)'%round(Ntotal.Integral(),3),'PL')
                l.AddEntry(Utotal,'up(%s)'%round(Utotal.Integral(),3),'PL')
                l.AddEntry(Dtotal,'down(%s)'%round(Dtotal.Integral(),3),'PL')
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
                Utotal.SetFillColor(0)
                Utotal.Draw("same hist")
                Dtotal.SetLineColor(2)
                Dtotal.SetLineStyle(3)
                Dtotal.SetLineWidth(2)
                Dtotal.SetFillColor(0)
                Dtotal.Draw("same hist")
                l.SetFillColor(0)
                l.SetBorderSize(0)
                l.Draw()

                title=myText('Shape Systematic %s in %s'%(syst,MC),0.17,0.85)

                print 'Shape Systematic %s in %s'%(syst,MC)
                print 'Up:     \t%s'%Utotal.Integral()
                print 'Nominal:\t%s'%Ntotal.Integral()
                print 'Down:   \t%s'%Dtotal.Integral()

                if not (Utotal.Integral() == 0 or Dtotal.Integral() == 0):

                    unten.cd()
                    ROOT.gPad.SetTicks(1,1)

                    nBins = Utotal.GetNbinsX()
                    #xMin = Utotal.GetXaxis().GetBinLowEdge(1)
                    #xMax = Utotal.GetXaxis().GetBinUpEdge(nBins-2)
                    xMin = Utotal.GetXaxis().GetBinLowEdge(1)
                    xMax = Utotal.GetXaxis().GetBinUpEdge(nBins)
                    ratioU, errorU  = getRatio(Utotal,Ntotal,xMin,xMax)
                    ratioD, errorD  = getRatio(Dtotal,Ntotal,xMin,xMax)

                    ksScoreU = Ntotal.KolmogorovTest( Utotal )
                    chiScoreU = Ntotal.Chi2Test( Utotal , "WWCHI2/NDF")
                    ksScoreD = Ntotal.KolmogorovTest( Dtotal )
                    chiScoreD = Ntotal.Chi2Test( Dtotal , "WWCHI2/NDF")


                    ratioU.SetStats(0)
                    #ratioU.GetYaxis().SetRangeUser(0.9,1.1)
                    ratioU.GetYaxis().SetRangeUser(0.6,1.4)
                    ratioU.GetYaxis().SetNdivisions(502,0)
                    ratioD.SetStats(0)
                    ratioD.GetYaxis().SetRangeUser(0.9,1.1)
                    ratioD.GetYaxis().SetNdivisions(502,0)
                    ratioD.GetYaxis().SetLabelSize(0.05)
                    ratioD.SetLineColor(2)
                    ratioD.SetMarkerStyle(0)
                    ratioD.SetLineStyle(3)
                    ratioD.SetLineWidth(2)
                    ratioU.SetLineColor(4)
                    ratioU.SetMarkerStyle(0)
                    ratioU.SetLineStyle(4)
                    ratioU.SetLineWidth(2)

                    fitRatioU = ratioU.Fit("pol2","S")
                    ratioU.GetFunction("pol2").SetLineColor(4)
                    fitRatioD = ratioD.Fit("pol2","S")
                    ratioU.Draw("SAME")
                    ratioD.GetXaxis().SetTitle('BDT Output')
                    ratioD.GetYaxis().SetTitle('Ratio')
                    ratioD.GetYaxis().SetTitleSize(0.1)
                    ratioD.GetYaxis().SetTitleOffset(0.2)
                    fitRatioU.Draw("SAME")
                    fitRatioD.Draw("SAME")
                    ratioD.Draw("SAME")

                #name = outpath+Abin+'_M'+mass+'_'+channel+'_'+MC+syst+'.png'
                #c.Print(name)
                name = outpath+channel+'/'+'systPlot_'+channel+'_M'+mass+'_'+channel+'_'+MC+syst+'.pdf'
                print 'name is', name
                #if not 'EWK' in name: sys.exit()
                #c.Print(name.replace('.pdf','.png'))
                c.SaveAs(name)


        input.Close()
