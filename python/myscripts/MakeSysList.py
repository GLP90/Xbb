import ROOT
import sys

# print list of all variations used in the training step
# configured for Wlv (2016)

ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch()

#nominal
#VarList_in = 'SYS_UD: H_mass_SYS_UD H_pt_SYS_UD V_pt abs(TVector2::Phi_mpi_pi(H_phi-V_phi)) Jet_btagCMVA[hJidxCMVA[1]] MET_pt_SYSUD abs(TVector2::Phi_mpi_pi(Alt$(Muon_phi[VMuonIdx[0]],0)+Alt$(Electron_phi[VElectronIdx[0]],0)-V_phi)) top_mass_SYS_UD V_mt Sum$(Jet_pt_SYSUD>25&&abs(Jet_eta)<2.5&&Jet_puId>0&&Jet_lepFilter&&Iteration$!=<!General|btagidx0!>&&Iteration$!=<!General|btagidx1!>) SA5'

#nominal
#VarList_in = 'SYS_UD: H_mass_SYS_UD H_pt_SYS_UD abs(TVector2::Phi_mpi_pi(H_phi-V_phi)) MET_pt_SYSUD (Jet_eta[hJidxCMVA[0]]-Jet_eta[hJidxCMVA[1]]) Jet_btagCMVA[hJidxCMVA[0]] Jet_btagCMVA[hJidxCMVA[1]] SA5 TVector2::Phi_mpi_pi(Jet_phi[hJidxCMVA[0]]-Jet_phi[hJidxCMVA[1]]) max(Jet_pt_SYSUD[hJidxCMVA[0]],Jet_pt_SYSUD[hJidxCMVA[1]]) min(Jet_pt_SYSUD[hJidxCMVA[0]],Jet_pt_SYSUD[hJidxCMVA[1]]) MaxIf$(Jet_btagCMVA,Jet_pt_SYSUD>30&&Jet_puId>=4&&Iteration$!=hJidxCMVA[0]&&Iteration$!=hJidxCMVA[1]) MaxIf$(Jet_pt_SYSUD,Jet_pt_SYSUD>30&&Jet_puId>=4&&Jet_lepFilter&&Iteration$!=hJidxCMVA[0]&&Iteration$!=hJidxCMVA[1]) MinIf$(abs(TVector2::Phi_mpi_pi(Jet_phi-V_phi))-3.1415,Jet_pt_SYSUD>30&&Jet_puId>=4)'

#VarList_in = 'SYS_UD: H_mass_noFSR_SYS_UD H_pt_noFSR_SYS_UD abs(TVector2::Phi_mpi_pi(H_phi_noFSR_SYS_UD-V_phi)) V_pt (Jet_eta[hJidxCMVA[0]]-Jet_eta[hJidxCMVA[1]]) Jet_btagCMVA[hJidxCMVA[0]] Jet_btagCMVA[hJidxCMVA[1]] SA5 TVector2::Phi_mpi_pi(Jet_phi[hJidxCMVA[0]]-Jet_phi[hJidxCMVA[1]]) max(Jet_PtReg[hJidxCMVA[0]]*Jet_pt_SYSUD[hJidxCMVA[0]]/Jet_Pt[hJidx[0]],Jet_PtReg[hJidxCMVA[1]]*Jet_pt_SYSUD[hJidxCMVA[1]]/Jet_Pt[hJidx[1]]) min(Jet_PtReg[hJidxCMVA[0]]*Jet_pt_SYSUD[hJidxCMVA[0]]/Jet_Pt[hJidx[0]],Jet_PtReg[hJidxCMVA[1]]*Jet_pt_SYSUD[hJidxCMVA[1]]/Jet_Pt[hJidx[1]]) MaxIf$(Jet_btagCMVA,Jet_pt_SYSUD>30&&Jet_puId>=4&&Iteration$!=hJidxCMVA[0]&&Iteration$!=hJidxCMVA[1]) MaxIf$(Jet_Pt,Jet_pt_SYSUD>30&&Jet_puId>=4&&Jet_lepFilter&&Iteration$!=hJidxCMVA[0]&&Iteration$!=hJidxCMVA[1]) MinIf$(abs(TVector2::Phi_mpi_pi(Jet_phi-V_phi))-3.1415,Jet_Pt>30&&Jet_puId>=4)'

#For Wlv BOOST
#inital
#VarList_in ': FatJet_msoftdrop[Hbb_fjidx] FatJet_pt[Hbb_fjidx] V_pt abs(TVector2::Phi_mpi_pi(FatJet_phi[Hbb_fjidx]-V_phi)) MET_Pt abs(VHbb::deltaPhi(MET_phi,Alt$((Vtype==2)*Muon_phi[VMuonIdx[0]],0)+Alt$((Vtype==3)*Electron_phi[VElectronIdx[0]],0))) V_mt Sum$(Jet_Pt>25&&abs(Jet_eta)<2.9&&Jet_puId>0&&Jet_lepFilter) SA5'

#VarList_in = 'SYS_UD: FatJet_msoftdrop_sys_SYS_UD FatJet_pt_sys_SYS_UD V_pt abs(TVector2::Phi_mpi_pi(FatJet_phi[Hbb_fjidx]-V_phi)) MET_pt_SYSUD abs(VHbb::deltaPhi(MET_phi_SYSUD,Alt$((Vtype==2)*Muon_phi[VMuonIdx[0]],0)+Alt$((Vtype==3)*Electron_phi[VElectronIdx[0]],0))) V_mt Sum$(Jet_pt_SYSUD>25&&abs(Jet_eta)<2.9&&Jet_puId>0&&Jet_lepFilter) SA5'


#WlvBDTBOOSTVarsFinal_nodB
#VarList_in =  'SYS_UD: FatJet_msoftdrop_sys_SYS_UD FatJet_pt_sys_SYS_UD MET_pt_SYSUD abs(VHbb::deltaPhi(MET_phi_SYSUD,Alt$((Vtype==2)*Muon_phi[VMuonIdx[0]],0)+Alt$((Vtype==3)*Electron_phi[VElectronIdx[0]],0))) V_mt SA5 FatJet_pt_sys_SYS_UD/V_pt abs(FatJet_eta[Hbb_fjidx]-V_eta)'
#
###[WlvBDTBOOSTVarsFinal_wdB]
VarList_in = 'SYS_UD: FatJet_msoftdrop_sys_SYS_UD FatJet_pt_sys_SYS_UD MET_pt_SYSUD abs(VHbb::deltaPhi(MET_phi_SYSUD,Alt$((Vtype==2)*Muon_phi[VMuonIdx[0]],0)+Alt$((Vtype==3)*Electron_phi[VElectronIdx[0]],0))) V_mt SA5 FatJet_pt_sys_SYS_UD/V_pt FatJet_btagHbb[Hbb_fjidx] abs(FatJet_eta[Hbb_fjidx]-V_eta)'



#List of the systematics
JECsys = [
        'jer',
        'jesAbsoluteStat',
        'jesAbsoluteScale',
        'jesAbsoluteFlavMap',
        'jesAbsoluteMPFBias',
        'jesFragmentation',
        'jesSinglePionECAL',
        'jesSinglePionHCAL',
        'jesFlavorQCD',
        'jesRelativeJEREC1',
        'jesRelativeJEREC2',
        'jesRelativeJERHF',
        'jesRelativePtBB',
        'jesRelativePtEC1',
        'jesRelativePtEC2',
        'jesRelativePtHF',
        'jesRelativeBal',
        'jesRelativeFSR',
        'jesRelativeStatFSR',
        'jesRelativeStatEC',
        'jesRelativeStatHF',
        'jesPileUpDataMC',
        'jesPileUpPtRef',
        'jesPileUpPtBB',
        'jesPileUpPtEC1',
        'jesPileUpPtEC2',
        'jesPileUpPtHF',
        'jesPileUpMuZero',
        'jesPileUpEnvelope',
        'minmax',
        #for Boost
        'jms',
        'jmr',

    ]

#JECsys = [
#        'JER', 
#        'PileUpDataMC',
#        'PileUpPtRef',
#        'PileUpPtBB',
#        'PileUpPtEC1',
#        'RelativeJEREC1',
#        'RelativeFSR',
#        'RelativeStatFSR',
#        'RelativeStatEC',
#        'RelativePtBB',
#        'RelativePtEC1',
#        'AbsoluteScale',
#        'AbsoluteMPFBias',
#        'AbsoluteStat',
#        'SinglePionECAL',
#        'SinglePionHCAL',
#        'Fragmentation',
#        'TimePtEta',
#        'FlavorQCD'
#]

#List of the variables affected by the sys
#VarSysDic= ['H_mass_SYS_UD','H_pt_SYS_UD', 'top_mass_SYS_UD','Sum$(Jet_pt_SYSUD>25&&abs(Jet_eta)<2.5&&Jet_puId>0&&Jet_lepFilter&&Iteration$!=<!General|btagidx0!>&&Iteration$!=<!General|btagidx1!>)']

VarList_new =  []
SysList = JECsys
UDList = ['Up','Down']
for syst in SysList:
    for ud in UDList:
        VarList = VarList_in
        #for var in VarSysDic:
        #    if not var in VarList:
        #        print 'var:', var, 'not found'
        #        print 'Aborting'
        #        sys.exit()
        #    VarList = VarList.replace(var,var+"_corr"+syst+ud)
        VarList = VarList.replace('SYS',syst)
        VarList = VarList.replace('UD',ud)
        VarList_new.append(VarList)

print '==========================='
print 'PRINTING Nominal'
print '==========================='
VarList_nominal = VarList_in
VarList_nominal = VarList_nominal.replace('_SYS_UD','').replace('_SYSUD','')
print VarList_nominal

print '==========================='
print 'PRINTING varlists'
print '==========================='
for var_new in VarList_new: 
    print var_new +'\n'

print '==========================='
print 'PRINTING systematicslist'
print '==========================='

systematics = 'systematics ='

for var_new in VarList_new: 
    systematics = systematics + ' ' +var_new.split(':')[0]
print systematics
