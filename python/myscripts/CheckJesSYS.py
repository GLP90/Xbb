
import ROOT
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch()

###
##Check the regression sys
###

#samples = ['root://t3dcachedb03.psi.ch//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/sys_v31/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_126_7a05575ff6ab3d0368f676db5ad00430b759f9e685c010cf41ca40df.root']

#samples = ['root://t3dcachedb03.psi.ch//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v32/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_126_7a05575ff6ab3d0368f676db5ad00430b759f9e685c010cf41ca40df.root']

#new
samples = ['root://t3dcachedb03.psi.ch//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v33/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/tree_arizzi-RunIIMoriond17-DeepAndR108_180517_164151_0000_42_b80af3072026a7212ed2a28dff002f08d9947e12a9e19e515f0075f5.root']

##TChain
t = ROOT.TChain('Events')
for sample in samples:
    print 'sample is', sample
    #t.Add(pathin_+sample+'/Events')
    t.Add(sample+'/Events')

##TFile
#f = ROOT.TFile.Open(pathin_)
#t = f.Get("tree")


#VarList = ['FatJet_msoftdrop_sys_SYS_UD',
#        'FatJet_pt_sys_SYS_UD',
#        'MET_pt_SYSUD',
#        'MET_phi_SYSUD',
#        'Jet_pt_SYSUD']

#VarList = ['BDT_Wlv_BOOST.SYS_UD']
#VarList = ['BDT_Wlv_BOOSTFinal_wdB.SYS_UD']
#VarList = ['BDT_Wlv_v7.SYS_UD']
VarList = ['BDT_Wlv_v8.SYS_UD']

#JECsys = ['jer','jesAbsoluteStat','jesAbsoluteScale','jesAbsoluteFlavMap','jesAbsoluteMPFBias','jesFragmentation','jesSinglePionECAL','jesSinglePionHCAL','jesFlavorQCD','jesRelativeJEREC1','jesRelativeJEREC2','jesRelativeJERHF','jesRelativePtBB','jesRelativePtEC1','jesRelativePtEC2','jesRelativePtHF','jesRelativeBal','jesRelativeFSR','jesRelativeStatFSR','jesRelativeStatEC','jesRelativeStatHF','jesPileUpDataMC','jesPileUpPtRef','jesPileUpPtBB','jesPileUpPtEC1','jesPileUpPtEC2','jesPileUpPtHF','jesPileUpMuZero','jesPileUpEnvelope','jesTotal']
JECsys = ['jms','jmr','jesAbsoluteStat','jesAbsoluteScale','jesPileUpPtEC2','jesRelativePtEC1', 'jesSinglePionHCAL', 'minmax']
#JECsys = ['jesAbsoluteStat']

SysList = JECsys
UDList = ['Up','Down']
#CatList = ['HighCentral','LowCentral','HighForward','LowForward']
AxisList = {'mass':[20,0,400],'msoft':[20,0,400],'HCSV_reg_pt':[20,0,400],'Phi':[20,-3.2, 3.2],'eta':[20,0,5],'FatJet_pt_sys':[20,0,1000],'Jet_Pt':[20,0,300],'Pt':[20,0,300],'CMVA':[20,-1,1],'BDT':[20,-1,1]}
for var in VarList:
    for syst in SysList:
        #for cat in CatList:
        c = ROOT.TCanvas('c','c',800,800) 
        pad1 = ROOT.TPad('pad1','pad1', 0, 0.3, 1, 1.0)
        pad1.SetBottomMargin(0)
        pad1.SetGridx()
        pad1.Draw()
        pad1.cd()

        nbin = 0
        xmin = 0
        xmax = 0
        #var_nom = var.replace('.SYS_UD','.Nominal').replace('.SYS_UD','.Nominal').replace('_SYSUD','').replace('_SYS','').replace('_UD','').replace('_CAT','').replace('_corr','').replace('.SYS_UD','.Nominal')
        var_nom = var.replace('FatJet_msoftdrop_sys_SYS_UD','FatJet_msoftdrop_sys').replace('FatJet_pt_sys_SYS_UD','FatJet_pt_sys').replace('MET_pt_SYSUD','MET_Pt').replace('MET_phi_SYSUD','MET_Phi').replace('Jet_pt_SYSUD','Jet_Pt').replace('BDT_Wlv_BOOST.SYS_UD','BDT_Wlv_BOOST.Nominal').replace('BDT_Wlv_v8.SYS_UD','BDT_Wlv_v8.Nominal')
        print 'var nom is', var_nom


        for axis in AxisList:
            if axis in var_nom:
                #nbin = AxisList[axis][0]
                xmin = AxisList[axis][1]
                xmax = AxisList[axis][2]
        #nbin = 100
        nbin = 20

        #for event in t:
        #    print getattr(t,var_nom)
        h_nom = ROOT.TH1D('h_nom','h_nom',nbin, xmin, xmax)
        #print 'var nom is', var_nom
        #if var_nom.startswith('Jet_pt'):
        #    if '_INDEX0'in var_nom: t.Draw(var_nom.replace('_INDEX0','[hJidxCMVA[0]]')+'>>h_nom')
        #    elif '_INDEX1'in var_nom: t.Draw(var_nom.replace('_INDEX1','[hJidxCMVA[1]]')+'>>h_nom')
        #else:
        #    t.Draw(var_nom+'>>h_nom')
        t.Draw(var_nom+'>>h_nom','Hbb_fjidx>-1')
        print 'Drawn'
        h_nom.SetLineColor(1)
        h_nom.SetMarkerStyle(20)
        h_nom.SetMarkerColor(1)
        h_nom.SetLineWidth(2)
        h_nom.Sumw2()

        h_ud = {} 
        for ud in UDList:
            #fill Dic
            SysDic = {}
            SysDic['var'] = var 
            SysDic['sys'] = syst
            SysDic['UD'] = ud 
            #SysDic['cat'] = cat 
            #SysDic['varname'] = var.replace('SYS',syst).replace('UD',ud).replace('CAT',cat)
            SysDic['varname'] = var.replace('SYS',syst).replace('UD',ud)
            #print 'do variations'
            #print 'var is', SysDic['varname']
            h_ud[ud] = ROOT.TH1D('h_%s'%ud,'h_%s'%ud,nbin, xmin, xmax)
            #if SysDic['varname'].startswith('Jet_pt'):
            #    if '_INDEX0'in SysDic['varname']: 
            #        t.Draw(SysDic['varname'].replace('_INDEX0','[hJCidx[0]]')+'>>h_%s'%ud)
            #    elif '_INDEX1'in SysDic['varname']: 
            #        t.Draw(SysDic['varname'].replace('_INDEX1','[hJCidx[1]]')+'>>h_%s'%ud)
            #else:
            #    t.Draw(SysDic['varname']+'>>h_%s'%ud)
            t.Draw(SysDic['varname']+'>>h_%s'%ud,'Hbb_fjidx>-1')

            #h_ud[ud].Draw('same')
            #t.Draw(SysDic['varname'])

        h_nom.Draw()
        h_nom.GetXaxis().SetTitle(var_nom)
        h_ud['Up'].Draw('same')
        h_ud['Up'].SetLineColor(4)
        h_ud['Up'].SetLineStyle(4)
        h_ud['Up'].SetLineWidth(2)
        h_ud['Up'].GetYaxis().SetNdivisions(505)
        h_ud['Up'].GetYaxis().SetTitleSize(20)
        h_ud['Up'].GetYaxis().SetTitleFont(43)
        h_ud['Up'].GetYaxis().SetTitleOffset(1.55)
        h_ud['Up'].GetYaxis().SetLabelFont(43)
        h_ud['Up'].GetYaxis().SetLabelSize(15)
        h_ud['Up'].GetXaxis().SetTitleSize(20)
        h_ud['Up'].GetXaxis().SetTitleFont(43)
        h_ud['Up'].GetXaxis().SetTitleOffset(4.)
        h_ud['Up'].GetXaxis().SetLabelFont(43)
        h_ud['Up'].GetXaxis().SetLabelSize(15)
        h_ud['Up'].GetXaxis().SetTitle(var_nom)

        h_ud['Down'].Draw('same')
        h_ud['Down'].SetLineColor(2)
        h_ud['Down'].SetLineStyle(2)
        h_ud['Down'].SetLineWidth(2)

        #print h_nom.GetEntries()
        #print h_ud['Down'].GetEntries()
        #print h_ud['Up'].GetEntries()


        leg = ROOT.TLegend(0.7, 0.8, 1 , 1)
        leg.AddEntry(h_nom,'nominal')
        leg.AddEntry(h_ud['Up'],'up')
        leg.AddEntry(h_ud['Down'],'down')
        leg.Draw('same')

        c.cd()
        pad2 = ROOT.TPad("pad2", "pad2", 0, 0.05, 1, 0.3)
        pad2.SetTopMargin(0)
        pad2.SetBottomMargin(0.2)
        pad2.SetGridx()
        pad2.SetGridy()
        pad2.Draw()
        pad2.cd()

        ratio_up =  h_ud['Up'].Clone()
        ratio_up.Divide(h_nom) 
        ratio_up.Draw()
        ratio_up.GetYaxis().SetRangeUser(0.9,1.1)
        ratio_down =  h_ud['Down'].Clone()
        ratio_down.Divide(h_nom) 
        ratio_down.Draw('same')

        #c.SaveAs('BDTCheck/'+SysDic['varname']+'.pdf')
        c.SaveAs('BDTCheck_new/'+SysDic['varname']+'.pdf')
        #c.SaveAs('WPlus/'+SysDic['varname']+'.pdf')
        #c.SaveAs('TT_SYSUpDown/'+SysDic['varname']+'.pdf')
        #c.SaveAs('TT_SYSUpDown/'+SysDic['varname']+'.png')
        #c.SaveAs('TT_SYSUpDown/'+SysDic['varname']+'.root')
        #c.SaveAs('TT_SYSUpDown/'+SysDic['varname']+'.C')

