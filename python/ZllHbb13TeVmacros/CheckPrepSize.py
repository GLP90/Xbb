###################################

#Goal: Loops for all the samples in the PREPouts and list their size

###################################

import os
import ROOT

#V20
_path1 = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V20/prep_v4/'
#V21
_path2 = '/pnfs/psi.ch/cms/trivcat/store/user/perrozzi/VHbb/ZllHbb13TeV_V21/preptest2/'

#Define list of cuts
CSV_Loose = '0.46'
CSV_Medium = '0.8'
CSV_Tight = '0.935'
pT20 = '(vLeptons_pt[0] > 20. & vLeptons_pt[1] > 20.)'
addjetV20 = 'Sum$(Jet_pt>20 && abs(Jet_eta)<2.4 && Jet_puId == 1)'
addjetV21 = 'Sum$(Jet_pt>20 && abs(Jet_eta)<2.4 && Jet_puId ==7)'
LooseIso =  '(vLeptons_relIso04[0] < 0.25 & vLeptons_relIso04[1] < 0.25)'

CRZlightV20 = '(V_mass > 75. & V_mass < 105. & Jet_pt[hJCidx[0]] > 20 & Jet_pt[hJCidx[1]] > 20 & HCSV_pt > 100 & Jet_btagCSV[hJCidx[0]] < '+ CSV_Tight + ' & Jet_btagCSV[hJCidx[1]] < '+ CSV_Tight + ' & ' + addjetV20 + ' == 2 & abs(HVdPhi) > 2.9 & ' + pT20 + ' & ' + LooseIso + ')'

CRZlightV21 = '(V_mass > 75. & V_mass < 105. & Jet_pt[hJCidx[0]] > 20 & Jet_pt[hJCidx[1]] > 20 & HCSV_pt > 100 & Jet_btagCSV[hJCidx[0]] < '+ CSV_Tight + ' & Jet_btagCSV[hJCidx[1]] < '+ CSV_Tight + ' & ' + addjetV21 + ' == 2 & abs(HVdPhi) > 2.9 & ' + pT20 + ' & ' + LooseIso + ')'

CRZb_incl = '(V_mass > 85. & V_mass < 97. & met_pt < 60 & Jet_pt[hJCidx[0]] > 20 & Jet_pt[hJCidx[1]] > 20 & (HCSV_mass < 90 || HCSV_mass > 145) & Jet_btagCSV[hJCidx[0]] > '+CSV_Tight + '& Jet_btagCSV[hJCidx[1]] > '+CSV_Loose+ ' & abs(HVdPhi) > 2.9 & '+pT20 + ' & ' + LooseIso + ')'

CRttbar_incl = '(Jet_pt[hJCidx[0]] > 20 & Jet_pt[hJCidx[1]] > 20 & HCSV_pt > 100 & V_mass > 10 & (V_mass < 75 || V_mass > 120) & Jet_btagCSV[hJCidx[0]] > ' + CSV_Tight + ' & Jet_btagCSV[hJCidx[1]] > ' +CSV_Loose + ' & ' + pT20 + ' & ' + LooseIso +')'

ZllBDThighVptcut = 'V_mass > 75 & V_mass < 105 & Jet_pt[hJCidx[0]] > 20 & Jet_pt[hJCidx[1]] > 20 & (HCSV_mass > 40 & HCSV_mass < 250) & V_pt > 100 & Jet_btagCSV[hJCidx[0]] > ' +CSV_Loose + ' & Jet_btagCSV[hJCidx[1]] > ' + CSV_Loose

CUTLISTV20 = [CRZlightV20, CRZb_incl, CRttbar_incl, ZllBDThighVptcut]
CUTLISTV21 = [CRZlightV21, CRZb_incl, CRttbar_incl, ZllBDThighVptcut]
LISTNAME = ['Zlf', 'Zhf', 'ttbar', 'SR']



FILE1 = os.listdir(_path1)
FILE2 = os.listdir(_path2)

for file1 in FILE1:
    if not '.root' in file1: continue
    print '#events in sample', file1
    file_found = False
    for k in range(0, len(CUTLISTV20)):
        f = ROOT.TFile.Open('root://t3dcachedb03.psi.ch:1094/' + _path1 + file1)
        t = f.Get("tree")
        print 'for cut', LISTNAME[k]
        #print len(f)
        print ' V20', t.GetEntries(CUTLISTV20[k])
        for file2 in FILE2:
            if not '.root' in file2: continue
            if file2 != file1: continue
            file_found = True
            f = ROOT.TFile.Open('root://t3dcachedb03.psi.ch:1094/' + _path2 + file2)
            t = f.Get("tree")
            #print len(f)
            print ' V21', t.GetEntries(CUTLISTV21[k])
    if not file_found: print 'No such file in V20'
    print ''




