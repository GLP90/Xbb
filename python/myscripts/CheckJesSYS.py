
import ROOT
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch()

###
##Check the regression sys
###

#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/TEST2/ZmmH.BestCSV.heppy.DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1.root'
#
#f = ROOT.TFile.Open(pathin_)
#t = f.Get("tree")
#
#
#VarList = ['HCSV_reg_corrSYSUD_mass_CAT','HCSV_reg_corrSYSUD_pt_CAT', 'HCSV_reg_corrSYSUD_eta_CAT', 'HCSV_reg_corrSYSUD_phi_CAT','Jet_pt_reg_corrSYSUD_CAT_INDEX0','Jet_pt_reg_corrSYSUD_CAT_INDEX1', 'Sum$(Jet_pt_reg_corrSYSUD_CAT>30&&abs(Jet_eta)<2.4&&Jet_puId==7&&Jet_id>0&&aJCidx!=(hJCidx[0])&&(aJCidx!=(hJCidx[1])))']

###
##Check the BDT sys
###

#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25/mva_v8_TEST/ggZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1/tree_VHBB_HEPPY_V25_ggZH_HToBB_ZToLL_M125_13TeV_powheg_Py8__RunIISummer16MAv2-PUMoriond17_80r2as_2016_TrancheIV_v6_ext1-v1_4_a4085e20b6f3529b24861250b2d0c6748eed84fb3c9aaa402e946fba.root'

#TT

# global path

#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/sys_deleteme/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/'
#pathin_ = '../'
pathin_ = ''

#samples = ['tree_arizzi-RunIIMoriond17-DeepAndR172_180517_171751_0000_1_b84d9a7c8da545216b5e2723b5e004384373dd3f5171681212e4f3b3.root']

#samples = ['root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v28//WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR173_180517_171824_0000_1_26314581f63a7696b701b20db798574a7ff16b0f453b790875e4fc97.root']

#samples = ['root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v28/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR172_180517_171751_0000_1_b84d9a7c8da545216b5e2723b5e004384373dd3f5171681212e4f3b3.root']
samples = ['root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR172_180517_171751_0000_1_b84d9a7c8da545216b5e2723b5e004384373dd3f5171681212e4f3b3.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_64_e6fdd2ae26f3f4f3b7d75227f4796e940e8a963f3ad9b57435d1975b.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_82_17e43b1ca7b61d2538927c061e353bfc4c24f6b7c6a2f64e3d717f3a.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_91_730e08f709d817a974901c3cf67349cf469a047fb156c58f93556cf5.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_1_ba7510e8d00ff2342b75294d393722e1b496ff20b5c37f79d631a9a6.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_117_d1a0684acc0e14fc8697be33af2b13492251df946aaad850b04024ae.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_37_b9996b644a07b160e1eee413490909dfae271658db39e8a9f408efa1.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_126_7a05575ff6ab3d0368f676db5ad00430b759f9e685c010cf41ca40df.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_28_7cd5911f7dc275a52184645bef1d865a1e3a8ae2272eb1ec6dade307.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_108_5779db05e30001366ac7f9495d85b217631cf03182934a76d1b893e0.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_19_b0b85a54c349151b657689e022365a316956e19bec0134e1ee30701c.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_55_0f65841083eb9e7a52e9f0b5f746d07e6ead131da7f27a798a4502dd.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_73_9a0d4f2d9a0811e2cda0809600b8ab60e97c4b3492848a6c6bbee342.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_46_f20faac835c18c85cc10398b9b19fa7d3d058c93fa772c408b85fb49.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_83_8be4241d83339c16ea01c2b4dbfeeca596af56a53ee2e37bfbf387e1.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_92_e5fe30704bb4badf3d6fb8d6579699b2211cff43b6c5e4d9f9e5a029.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_65_5436b4c1158c08d64feef3ca3908d72e3cecd6255924e19fe6964ba5.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_10_86907b50ce9e54b8c28fceb70eee61560daad8eb0f991aff27de0b5b.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_109_d3dd80abc012e752fc51969c1694e9ce86479e8abb1d0723e7550f07.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_127_e783e90fd25a87d47a6a15542d9fd9ad8c681cdeb3458aa834a37d33.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_38_93ca37f4a0561d19f5fdafe98f40fa579ccb485107153d1c20e1a12a.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_56_46cb2416b8271bfca014a486880c6f71d38c1414a5d2f476372111f8.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_29_7d1940cc8664dd8f6ca4bc897d5e0471eab42ac32507cd8b736c6993.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_2_dca9765a4dff130cd377d6096373d0a71c2966254ee7dc29ec799bde.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_47_b4919e914247118756594805c9dc321902cb22ffd01974fb50cae955.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_74_a0cca1f5c13cf0942905ff120e2d0ae0d1eacce4cf9e0de39390b847.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_118_f9496d110cf6bbfbbfe170006249a59d43a9c43004a9af31589bafac.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_84_19e62b69e6894d0d2a28ba81509feccd1ce8cf61258c401d6404c368.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_93_93bf17276ffc2f1adf435596621f55bf4cd2e56f71cecb2671ef1e24.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_66_321db0f8537b20be16ba0778f1f090e195756971cf9ea13f04cdebee.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_128_2bf811164b3e3e8d087eb4f1a7fa09b5a999759fe98aa684187708b7.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_100_2ae7c832d813c876a33c844b4f905ccea9ea676d4470cf60dc37b013.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_11_7925706321f1ffe64347b9219a2a58b4d57396bb7900799325089cfd.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_39_3254d9154162f0100fd32aca328a597e1747cc5146eda5594f79783e.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_57_2f935710409cf32488ecdbe888aee81e3c1020539bad69e24ce5a248.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_48_0c82da09e625150083bfd16e3bfbd06b07b653b747ff0e5ed11443bf.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_119_df5163e2f3fea8d2e618ed63b85aa3852951105b44afdadd077a3916.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_75_ea6da9752f2741ce0df6ae894e1f451b9c7ac3afbc0f60a144c1e680.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_3_1d2b228314ac72750bb930f43cc35fd17688fe791fec4b592e151e2b.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_129_bf86828fd3156caf202a78c3e0dec9e1ae1ad27772e4663b4a51edda.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_20_4ae53cd7a6bd21679c4a559c63753544afb3debe0f32adac82b50b48.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_85_9436bfb291d062373c8e143d27dad7fe7a605ba0efab664e1604bcae.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_94_c3daeb55445ac5246fd6c688133762c5360c55c7b2a91fea9ff477d0.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_67_21586f50ff75a9175941a159db01900f0d6e2485a50313f7992b44ed.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_110_396ea7b5b6310070ed93e708e851449349093de32ec6aa5092bea62a.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_101_14a73a20d6447f575b0b3057ec6fab50b9c5b1295b910f7c59508efe.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_12_fa5e1ae1081c9df6463785d845d5b01def4d6f6cae4189638da52f8d.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_4_833db14465286b21b71550dcae1a67cd401b9e9fb16148b3fa44e2a4.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_58_e4d0a85e8054bb32a8f4064ca89a4742cd537ba41398445a6d3000d0.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_30_043c099a8fd1bf42550488240658e9cc294d4ffbd2606b12a9816a3d.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_49_883a08d815a10e32bbf4d1500b631390d2cd4ff97868d4629f0c6aab.root',
#    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_76_17efce8f690e579f893474082a8e59256096cf6a21450c3189558af4.root',
    'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/VHbbPostNano2016/Wlv_v2/mva_v29/WplusH_HToBB_WToLNu_M125_13TeV_powheg_pythia8/tree_arizzi-RunIIMoriond17-DeepAndR133_180517_165540_0000_21_cc70d9420a899f4639639f9ec18cd0605621c755241c93712a16b4a8.root']

##TChain
t = ROOT.TChain('Events')
for sample in samples:
    print 'sample is', sample
    #t.Add(pathin_+sample+'/Events')
    t.Add(sample+'/Events')

#import sys
#sys.exit()

##TFile
#f = ROOT.TFile.Open(pathin_)
#t = f.Get("tree")


#VarList = ['FatJet_msoftdrop_sys_SYS_UD',
#        'FatJet_pt_sys_SYS_UD',
#        'MET_pt_SYSUD',
#        'MET_phi_SYSUD',
#        'Jet_pt_SYSUD']

#VarList = ['BDT_Wlv_BOOST.SYS_UD']
VarList = ['BDT_Wlv_BOOSTFinal_wdB.SYS_UD']

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
        var_nom = var.replace('FatJet_msoftdrop_sys_SYS_UD','FatJet_msoftdrop_sys').replace('FatJet_pt_sys_SYS_UD','FatJet_pt_sys').replace('MET_pt_SYSUD','MET_Pt').replace('MET_phi_SYSUD','MET_Phi').replace('Jet_pt_SYSUD','Jet_Pt').replace('BDT_Wlv_BOOST.SYS_UD','BDT_Wlv_BOOST.Nominal')
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

        c.SaveAs('BDTCheck/'+SysDic['varname']+'.pdf')
        #c.SaveAs('WPlus/'+SysDic['varname']+'.pdf')
        #c.SaveAs('TT_SYSUpDown/'+SysDic['varname']+'.pdf')
        #c.SaveAs('TT_SYSUpDown/'+SysDic['varname']+'.png')
        #c.SaveAs('TT_SYSUpDown/'+SysDic['varname']+'.root')
        #c.SaveAs('TT_SYSUpDown/'+SysDic['varname']+'.C')

