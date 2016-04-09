#!/usr/bin/env python
import os, sys, ROOT, warnings, pickle
ROOT.gROOT.SetBatch(True)
from array import array
from math import sqrt
from copy import copy, deepcopy
#suppres the EvalInstace conversion warning bug
warnings.filterwarnings( action='ignore', category=RuntimeWarning, message='creating converter.*' )
from optparse import OptionParser
from myutils import BetterConfigParser, Sample, progbar, printc, ParseInfo, Rebinner, HistoMaker

def useSpacesInDC(fileName):
    file_ = open(fileName,"r+")

    old = file_.read()
    ## get the maximum width of each colum (excluding the first lines)
    lineN = 0
    maxColumnWidth = [0]
    for line in old.split('\n'):
        lineN += 1
        if lineN<10: continue #skip the first 10 lines
        words = line.split('\t')
        for i in range(len(words)):
            if i>=len(maxColumnWidth): maxColumnWidth.append(0)
            if len(words[i])>maxColumnWidth[i]: maxColumnWidth[i]=len(words[i])
    ## replace the tabs with the new formatting (excluding the first lines)
    #newfile = open("newFile.txt","w+")
    lineN = 0
    file_.seek(0)
    for line in old.split('\n'):
        lineN += 1
        if lineN<10: #in the first 10 lines just replace '\t' with ' '
            file_.write(line.replace('\t',' ')+'\n')
            continue
        words = line.split('\t')
        newLine=""
        for i in range(len(words)): #use the new format!
            newLine += words[i].ljust(maxColumnWidth[i]+1)
        file_.write(newLine+'\n')
    file_.close()
    return

print '_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_'
print 'START DATACARD (workspace_datacard)'
print '_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_\n'

#--CONFIGURE---------------------------------------------------------------------

print 'Reading configuration files'
print '===========================\n'

argv = sys.argv
parser = OptionParser()
parser.add_option("-V", "--variable", dest="variable", default="",
                      help="variable for shape analysis")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
(opts, args) = parser.parse_args(argv)
config = BetterConfigParser()
config.read(opts.config)
var=opts.variable
#-------------------------------------------------------------------------------

#--read variables from config---------------------------------------------------
# 7 or 8TeV Analysis

print "Compile external macros"
print "=======================\n"

# compile external macros to compute variables on the fly
#ROOT.gSystem.CompileMacro("../plugins/PU.C")

print 'Assigne variables from  config'
print '==============================\n'

anaTag = config.get("Analysis","tag")
if not any([anaTag == '7TeV',anaTag == '8TeV',anaTag == '13TeV']):
    raise Exception("anaTag %s unknown. Specify 8TeV or 7TeV or 13TeV in the general config"%anaTag)
# Directories:
Wdir=config.get('Directories','Wdir')
vhbbpath=config.get('Directories','vhbbpath')
samplesinfo=config.get('Directories','samplesinfo')
path = config.get('Directories','dcSamples')
outpath=config.get('Directories','limits')
try:
    os.stat(outpath)
except:
    os.mkdir(outpath)
# parse histogram config:
treevar = config.get('dc:%s'%var,'var')
name = config.get('dc:%s'%var,'wsVarName')
title = name
# set binning
nBins = int(config.get('dc:%s'%var,'range').split(',')[0])
xMin = float(config.get('dc:%s'%var,'range').split(',')[1])
xMax = float(config.get('dc:%s'%var,'range').split(',')[2])
ROOToutname = config.get('dc:%s'%var,'dcName')
RCut = config.get('dc:%s'%var,'cut')
signals = config.get('dc:%s'%var,'signal').split(' ')
datas = config.get('dc:%s'%var,'dcBin')
Datacardbin=config.get('dc:%s'%var,'dcBin')
anType = config.get('dc:%s'%var,'type')
setup=eval(config.get('LimitGeneral','setup'))

import os
if os.path.exists("../interface/DrawFunctions_C.so"):
    print 'ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")'
    ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")

if os.path.exists("../interface/VHbbNameSpace_h.so"):
    print 'ROOT.gROOT.LoadMacro("../interface/VHbbNameSpace_h.so")'
    ROOT.gROOT.LoadMacro("../interface/VHbbNameSpace_h.so")

print "Using",('dc:%s'%var,'var')
print name
print title
print nBins
print xMin
print xMax
print ROOToutname
print RCut
print signals
print datas
print Datacardbin
print anType
print setup

#Systematics:
if config.has_option('LimitGeneral','addSample_sys'):
    addSample_sys = eval(config.get('LimitGeneral','addSample_sys'))
    additionals = [addSample_sys[key] for key in addSample_sys]
else:
    addSample_sys = None
    additionals = []
#find out if BDT or MJJ:
bdt = False
mjj = False
cr = False
if str(anType) == 'BDT':
    bdt = True
    systematics = eval(config.get('LimitGeneral','sys_BDT'))
elif str(anType) == 'Mjj':
    mjj = True
    systematics = eval(config.get('LimitGeneral','sys_Mjj'))
elif str(anType) == 'cr':
    cr = True
    systematics = eval(config.get('LimitGeneral','sys_cr'))
else:
    print 'EXIT: please specify if your datacards are BDT, Mjj or cr.'
    sys.exit()

sys_cut_suffix=eval(config.get('LimitGeneral','sys_cut_suffix'))
sys_weight_corr=eval(config.get('LimitGeneral','sys_weight_corr'))
sys_cut_include=[]
if config.has_option('LimitGeneral','sys_cut_include'):
    sys_cut_include=eval(config.get('LimitGeneral','sys_cut_include'))
systematicsnaming = eval(config.get('LimitGeneral','systematicsnaming'))
sys_factor_dict = eval(config.get('LimitGeneral','sys_factor'))
sys_affecting = eval(config.get('LimitGeneral','sys_affecting'))
# weightF:
weightF = config.get('Weights','weightF')
if str(anType) == 'cr': weightF_systematics = eval(config.get('LimitGeneral','weightF_sys_CR'))
else: weightF_systematics = eval(config.get('LimitGeneral','weightF_sys'))
# rescale stat shapes by sqrtN
rescaleSqrtN=eval(config.get('LimitGeneral','rescaleSqrtN'))
# get nominal cutstring:
treecut = config.get('Cuts',RCut)
# Train flag: splitting of samples
TrainFlag = eval(config.get('Analysis','TrainFlag'))
# toy data option:
toy=eval(config.get('LimitGeneral','toy'))
# blind data option:
blind=eval(config.get('LimitGeneral','blind'))
# additional blinding cut:
addBlindingCut = None
if config.has_option('LimitGeneral','addBlindingCut'):
    addBlindingCut = config.get('LimitGeneral','addBlindingCut')
    print 'adding add. blinding cut'
#change nominal shapes by syst
change_shapes = None
if config.has_option('LimitGeneral','change_shapes'):
    change_shapes = eval(config.get('LimitGeneral','change_shapes'))
    print 'changing the shapes'
#on control region cr never blind. Overwrite whatever is in the config
if str(anType) == 'cr':
    if blind:
        print '@WARNING: Changing blind to false since you are running for control region.'
    blind = False
if blind: 
    printc('red','', 'I AM BLINDED!')    
#get List of backgrounds in use:
backgrounds = eval(config.get('LimitGeneral','BKG'))
#Groups for adding samples together
GroupDict = eval(config.get('LimitGeneral','Group'))
#naming for DC
Dict= eval(config.get('LimitGeneral','Dict'))
#treating statistics bin-by-bin:
binstat = eval(config.get('LimitGeneral','binstat'))
# Use the rebinning:
rebin_active=eval(config.get('LimitGeneral','rebin_active'))
if str(anType) == 'cr':
    if rebin_active:
        print '@WARNING: Changing rebin_active to false since you are running for control region.'
    rebin_active = False
# ignore stat shapes
ignore_stats = eval(config.get('LimitGeneral','ignore_stats'))
#max_rel = float(config.get('LimitGeneral','rebin_max_rel'))
signal_inject=config.get('LimitGeneral','signal_inject')
# add signal as background
add_signal_as_bkg=config.get('LimitGeneral','add_signal_as_bkg')
if not add_signal_as_bkg == 'None':
    setup.append(add_signal_as_bkg)
#----------------------------------------------------------------------------

#--Setup--------------------------------------------------------------------
#Assign Pt region for sys factors
print 'Assign Pt region for sys factors'
print '================================\n'

if 'HighPtLooseBTag' in ROOToutname:
    pt_region = 'HighPtLooseBTag'
elif 'HighPt' in ROOToutname or 'highPt' in ROOToutname or 'highpt' in ROOToutname:
    pt_region = 'HighPt'
elif 'MedPt' in ROOToutname:
    pt_region = 'MedPt'
elif 'LowPt' in ROOToutname or 'lowPt' in ROOToutname or 'lowpt' in ROOToutname:
    pt_region = 'LowPt'
elif 'ATLAS' in ROOToutname:
    pt_region = 'HighPt'
elif 'MJJ' in ROOToutname:
    pt_region = 'HighPt' 
else:
    print "Unknown Pt region"
    pt_region = 'NoSysRegion'
    #sys.exit("Unknown Pt region")
# Set rescale factor of 2 in case of TrainFalg
if TrainFlag:
    MC_rescale_factor=2.
    print 'I RESCALE BY 2.0'
else: MC_rescale_factor = 1.
#systematics up/down
UD = ['Up','Down']

print 'Parse the sample information'
print '============================\n'
#Parse samples configuration
info = ParseInfo(samplesinfo,path)
# get all the treeCut sets
# create different sample Lists

print 'Get the sample list'
print '===================\n'
all_samples = info.get_samples(signals+backgrounds+additionals)
print 'workspace_datacard-all_samples:',[job.name for job in all_samples]

signal_samples = info.get_samples(signals) 
print 'signal samples:',[job.name for job in signal_samples]

background_samples = info.get_samples(backgrounds) 
data_sample_names = config.get('dc:%s'%var,'data').split(' ')
data_samples = info.get_samples(data_sample_names)

print 'The signal sample list is\n'
for samp in signal_samples:
    print samp
    print ''
print 'The background sample list is\n'
for samp in background_samples:
    print samp
    print ''
print 'The data samples are' 
for samp in data_samples:
    print samp
    print '' 
#-------------------------------------------------------------------------------------------------

optionsList=[]

def appendList(): optionsList.append({'cut':copy(_cut),'var':copy(_treevar),'name':copy(_name),'nBins':nBins,'xMin':xMin,'xMax':xMax,'weight':copy(_weight),'blind':blind})

#nominal
_cut = treecut
_treevar = treevar
_name = title
_weight = weightF
appendList()

print "Using weightF:",weightF
print 'Assign the systematics'
print '======================\n'

import os
if os.path.exists("../interface/DrawFunctions_C.so"):
    print 'ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")'
    ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")

#the 4 sys
for syst in systematics:
    for Q in UD:
        #default:
        _cut = treecut
        _name = title
        _weight = weightF
        #replace cut string
        new_cut=sys_cut_suffix[syst]
        if not new_cut == 'nominal':
            old_str,new_str=new_cut.split('>')
            _cut = treecut.replace(old_str,new_str.replace('?',Q))
            _name = title
            _weight = weightF
        if syst in sys_weight_corr:
            _weight = config.get('Weights',sys_weight_corr[syst]+'_%s' %(Q.upper()))
        #replace tree variable
        if bdt == True:
            #ff[1]='%s_%s'%(sys,Q.lower())
            _treevar = treevar.replace('.nominal','.%s_%s'%(syst,Q.lower()))
            _treevar = treevar.replace('.Nominal','.%s_%s'%(syst,Q.lower()))
            print _treevar
        elif mjj == True:
            if syst == 'JER' or syst == 'JES':
                _treevar = 'H_%s.mass_%s'%(syst,Q.lower())
            else:
                _treevar = treevar
        elif cr == True:
            #commented out, since shape sys are done using weights
            #if syst == 'beff' or syst == 'bmis' or syst == 'beff1':
            #    _treevar = treevar.replace(old_str,new_str.replace('?',Q))
            #else:
            #    _treevar = treevar
            _treevar = treevar
        #append
        appendList()

#UEPS
#Appends options for each weight 
for weightF_sys in weightF_systematics:
    for _weight in [config.get('Weights','%s_UP' %(weightF_sys)),config.get('Weights','%s_DOWN' %(weightF_sys))]:
        _cut = treecut
        _treevar = treevar
        _name = title
        appendList()

#print '===================\n'
#print 'The option list is', optionsList


print 'Preparations for Histograms (HistoMakeri)'
print '=========================================\n'

mc_hMaker = HistoMaker(all_samples,path,config,optionsList,GroupDict)
data_hMaker = HistoMaker(data_samples,path,config,[optionsList[0]])

print 'Calculate luminosity'
print '====================\n'
#Calculate lumi
lumi = 0.
nData = 0
for job in data_samples:
    nData += 1
    lumi += float(job.lumi)

if nData > 1:
    lumi = lumi/float(nData)

mc_hMaker.lumi = lumi
data_hMaker.lumi = lumi

if addBlindingCut:
    for i in range(len(mc_hMaker.optionsList)):
        mc_hMaker.optionsList[i]['cut'] += ' & %s' %addBlindingCut
    for i in range(len(data_hMaker.optionsList)):
        data_hMaker.optionsList[i]['cut'] += ' & %s' %addBlindingCut


if rebin_active:
    print "background_samples: ",background_samples
    mc_hMaker.calc_rebin(background_samples)
    #transfer rebinning info to data maker
    data_hMaker.norebin_nBins = copy(mc_hMaker.norebin_nBins)
    data_hMaker.rebin_nBins = copy(mc_hMaker.rebin_nBins)
    data_hMaker.nBins = copy(mc_hMaker.nBins)
    data_hMaker._rebin = copy(mc_hMaker._rebin)
    data_hMaker.mybinning = deepcopy(mc_hMaker.mybinning)

all_histos = {}
data_histos = {}

print '\n\t...fetching histos...\n'

### ORIGINAL ###
#for job in all_samples:
#    print '\t- %s'%job
#    if not GroupDict[job.name] in sys_cut_include:
#        # manual overwrite
#        if addBlindingCut:
#            all_histos[job.name] = mc_hMaker.get_histos_from_tree(job,treecut+'& %s'%addBlindingCut)
#        else:
#            all_histos[job.name] = mc_hMaker.get_histos_from_tree(job,treecut)
#    else:
#        all_histos[job.name] = mc_hMaker.get_histos_from_tree(job)

inputs=[]
for job in all_samples:
#   print 'job.name'
    cutOverWrite = None
    if not GroupDict[job.name] in sys_cut_include:
        if addBlindingCut:
            cutOverWrite = treecut +' & ' + addBlindingCut
        else:
            cutOverWrite = treecut
    inputs.append((mc_hMaker,"get_histos_from_tree",(job,cutOverWrite)))

# multiprocess=0
# if('pisa' in config.get('Configuration','whereToLaunch')):
multiprocess=int(config.get('Configuration','nprocesses'))
outputs = []
if multiprocess>1:
    from multiprocessing import Pool
    from myutils import GlobalFunction
    p = Pool(multiprocess)
    print 'launching get_histos_from_tree with ',multiprocess,' processes'
    outputs = p.map(GlobalFunction, inputs)
else:
    print 'launching get_histos_from_tree with ',multiprocess,' processes'
    for input_ in inputs:
        outputs.append(getattr(input_[0],input_[1])(*input_[2])) #ie. mc_hMaker.get_histos_from_tree(job,cutOverWrite)

for i,job in enumerate(all_samples):
    all_histos[job.name] = outputs[i]

#for job in all_samples:
#    print '\t- %s'%job
#    if not GroupDict[job.name] in sys_cut_include:
#        # manual overwrite
#        if addBlindingCut:
#            all_histos[job.name] = mc_hMaker.get_histos_from_tree(job,treecut+'& %s'%addBlindingCut)
#        else:
#            all_histos[job.name] = mc_hMaker.get_histos_from_tree(job,treecut)
#    else:
#        all_histos[job.name] = mc_hMaker.get_histos_from_tree(job)



#for job in all_samples:
#    print '\t- %s'%job
#    if not GroupDict[job.name] in sys_cut_include:
#        # manual overwrite
#        if addBlindingCut:
#            all_histos[job.name] = mc_hMaker.get_histos_from_tree(job,treecut+'& %s'%addBlindingCut)
#        else:
#            all_histos[job.name] = mc_hMaker.get_histos_from_tree(job,treecut)
#    else:
#        all_histos[job.name] = mc_hMaker.get_histos_from_tree(job)

for job in data_samples:
    print '\t- %s'%job
    data_histos[job.name] = data_hMaker.get_histos_from_tree(job)[0]['DATA']

print '\t> done <\n'

print 'Get the bkg histo'
print '=================\n'
i=0
for job in background_samples: 
    print job.name
    htree = all_histos[job.name][0].values()[0]
    if not i: 
        hDummy = copy(htree) 
    else: 
        hDummy.Add(htree,1) 
    del htree 
    i+=1
#?
if signal_inject:
    signal_inject = info.get_samples([signal_inject])
    sig_hMaker = HistoMaker(signal_inject,path,config,optionsList,GroupDict)
    sig_hMaker.lumi = lumi
    if rebin_active:
        sig_hMaker.norebin_nBins = copy(mc_hMaker.norebin_nBins)
        sig_hMaker.rebin_nBins = copy(mc_hMaker.rebin_nBins)
        sig_hMaker.nBins = copy(mc_hMaker.nBins)
        sig_hMaker._rebin = copy(mc_hMaker._rebin)
        sig_hMaker.mybinning = deepcopy(mc_hMaker.mybinning)

print 'Get the signal histo'
print '====================\n'
for job in signal_inject: 
    htree = sig_hMaker.get_histos_from_tree(job)
    hDummy.Add(htree[0].values()[0],1) 
    del htree 

print 'Get the data histo'
print '==================\n'
nData = 0
for job in data_histos:
    if nData == 0:
        theData = data_histos[job]
        nData = 1
    else:
        theData.Add(data_histos[job])

#print 'theData is', theData
#theData.Print()
#print 'First theData element'
#theData['data_SM_2015C'].Print()
#print 'Second theData element'
#theData['data_SM_2015D_topup'].Print()
#print 'Third theData element'
#theData['data_SM_2015D_1280'].Print()


print 'END DEBUG'


#-- Write Files-----------------------------------------------------------------------------------
# generate the TH outfile:
print 'Start writing the files'
print '=======================\n'

print 'Creating output file'
print '====================\n'
outfile = ROOT.TFile(outpath+'vhbb_TH_'+ROOToutname+'.root', 'RECREATE')
outfile.mkdir(Datacardbin,Datacardbin)
outfile.cd(Datacardbin)
# generate the Workspace:
WS = ROOT.RooWorkspace('%s'%Datacardbin,'%s'%Datacardbin) #Zee
print 'WS initialized'
disc= ROOT.RooRealVar(name,name,xMin,xMax)
obs = ROOT.RooArgList(disc)
#
ROOT.gROOT.SetStyle("Plain")

#order and add all together
final_histos = {}

print '\n\t--> Ordering and Adding Histos\n'

print 'workspace_datacard-all_samples:',[all_histos['%s'%job][0] for job in all_samples]

jobnames = [job.name for job in all_samples]

#NOMINAL:
final_histos['nominal'] = HistoMaker.orderandadd([all_histos['%s'%job][0] for job in all_samples],setup)

#SYSTEMATICS:
ind = 1
#print 'systematics is', systematics

print 'all_histos[job.name]',all_histos[job.name]
print 'len(all_histos[job.name])',len(all_histos[job.name])

print 'add UD sys'
print '==========\n'
for syst in systematics:
    for Q in UD:
        final_histos['%s_%s'%(systematicsnaming[syst],Q)] = HistoMaker.orderandadd([all_histos[job.name][ind] for job in all_samples],setup)
        ind+=1
print 'add weight sys'
print '==============\n'
for weightF_sys in weightF_systematics: 
    for Q in UD:
        final_histos['%s_%s'%(systematicsnaming[weightF_sys],Q)]= HistoMaker.orderandadd([all_histos[job.name][ind] for job in all_samples],setup)
        ind+=1
#?
if change_shapes:
    for key in change_shapes:
        syst,val=change_shapes[key].split('*')
        final_histos[syst][key].Scale(float(val))
        print 'scaled %s times %s val'%(syst,val)


def get_alternate_shape(hNominal,hAlternate):
    hVar = hAlternate.Clone()
    hNom = hNominal.Clone()
    hAlt = hNom.Clone()
    hNom.Add(hVar,-1.)
    hAlt.Add(hNom)
    for bin in range(0,hNominal.GetNbinsX()+1):
        if hAlt.GetBinContent(bin) < 0.: hAlt.SetBinContent(bin,0.)
    return hVar,hAlt

def get_alternate_shapes(all_histos,asample_dict,all_samples):
    alternate_shapes_up = []
    alternate_shapes_down = []
    for job in all_samples:
        nominal = all_histos[job.name][0]
        if job.name in asample_dict:
            alternate = copy(all_histos[asample_dict[job.name]][0])
            hUp, hDown = get_alternate_shape(nominal[nominal.keys()[0]],alternate[alternate.keys()[0]])
            alternate_shapes_up.append({nominal.keys()[0]:hUp})
            alternate_shapes_down.append({nominal.keys()[0]:hDown})
        else:
            newh=nominal[nominal.keys()[0]].Clone('%s_%s_Up'%(nominal[nominal.keys()[0]].GetName(),'model'))
            alternate_shapes_up.append({nominal.keys()[0]:nominal[nominal.keys()[0]].Clone()})
            alternate_shapes_down.append({nominal.keys()[0]:nominal[nominal.keys()[0]].Clone()})
    return alternate_shapes_up, alternate_shapes_down
        
if addSample_sys: 
    print 'Adding the samples systematics'
    print '==============================\n'
    aUp, aDown = get_alternate_shapes(all_histos,addSample_sys,all_samples)
    final_histos['%s_Up'%(systematicsnaming['model'])]= HistoMaker.orderandadd(aUp,setup)
    del aUp
    final_histos['%s_Down'%(systematicsnaming['model'])]= HistoMaker.orderandadd(aDown,setup)


if not ignore_stats:
    #make statistical shapes:
    print 'Make the statistical shapes'
    print '===========================\n'
    if not binstat:
        for Q in UD:
            final_histos['%s_%s'%(systematicsnaming['stats'],Q)] = {}
        for job,hist in final_histos['nominal'].items():
            errorsum=0
            for j in range(hist.GetNbinsX()+1):
                errorsum=errorsum+(hist.GetBinError(j))**2
            errorsum=sqrt(errorsum)
            total=hist.Integral()
            for Q in UD:
                final_histos['%s_%s'%(systematicsnaming['stats'],Q)][job] = hist.Clone()
                for j in range(hist.GetNbinsX()+1):
                    if Q == 'Up':
                        if rescaleSqrtN and total:
                            final_histos['%s_%s'%(systematicsnaming['stats'],Q)][job].SetBinContent(j,max(0,hist.GetBinContent(j)+hist.GetBinError(j)/total*errorsum))
                        else:
                            final_histos['%s_%s'%(systematicsnaming['stats'],Q)][job].SetBinContent(j,max(0,hist.GetBinContent(j)+hist.GetBinError(j)))
                    if Q == 'Down':
                        if rescaleSqrtN and total:
                            final_histos['%s_%s'%(systematicsnaming['stats'],Q)][job].SetBinContent(j,max(0,hist.GetBinContent(j)-hist.GetBinError(j)/total*errorsum))
                        else:
                            final_histos['%s_%s'%(systematicsnaming['stats'],Q)][job].SetBinContent(j,max(0,hist.GetBinContent(j)-hist.GetBinError(j)))
    else:
        print "Running Statistical uncertainty"
        threshold =  0.5 #stat error / sqrt(value). It was 0.5
        print "threshold",threshold
        binsBelowThreshold = {}
        for bin in range(1,nBins+1):
            for Q in UD:
                final_histos['%s_bin%s_%s'%(systematicsnaming['stats'],bin,Q)] = {}
            for job,hist in final_histos['nominal'].items():
                if not job in binsBelowThreshold.keys(): binsBelowThreshold[job] = []
                print "binsBelowThreshold",binsBelowThreshold
                print "hist.GetBinContent(bin)",hist.GetBinContent(bin)
                print "hist.GetBinError(bin)",hist.GetBinError(bin)
                if hist.GetBinContent(bin) > 0.:
                    if hist.GetBinError(bin)/sqrt(hist.GetBinContent(bin)) > threshold and hist.GetBinContent(bin) >= 1.:
                        binsBelowThreshold[job].append(bin)
                    elif hist.GetBinError(bin)/(hist.GetBinContent(bin)) > threshold and hist.GetBinContent(bin) < 1.:
                        binsBelowThreshold[job].append(bin)
                for Q in UD:
                    final_histos['%s_bin%s_%s'%(systematicsnaming['stats'],bin,Q)][job] = hist.Clone()
                    if Q == 'Up':
                        final_histos['%s_bin%s_%s'%(systematicsnaming['stats'],bin,Q)][job].SetBinContent(bin,max(0,hist.GetBinContent(bin)+hist.GetBinError(bin)))
                    if Q == 'Down':
                        final_histos['%s_bin%s_%s'%(systematicsnaming['stats'],bin,Q)][job].SetBinContent(bin,max(1.E-6,hist.GetBinContent(bin)-hist.GetBinError(bin)))


#print "binsBelowThreshold:",binsBelowThreshold
print 'Start writing shapes in WS'
print '==========================\n'
#write shapes in WS:
for key in final_histos:
    for job, hist in final_histos[key].items():
        if 'nominal' == key:
            hist.SetName('%s'%(Dict[job]))
            hist.Write()
            rooDataHist = ROOT.RooDataHist('%s' %(Dict[job]),'%s'%(Dict[job]),obs, hist)
            getattr(WS,'import')(rooDataHist)
        for Q in UD:
            if Q in key:
                theSyst = key.replace('_%s'%Q,'')
            else:
                continue
            if systematicsnaming['stats'] in key:
                nameSyst = '%s_%s_%s' %(theSyst,Dict[job],Datacardbin)
            elif systematicsnaming['model'] in key:
                nameSyst = '%s_%s' %(theSyst,Dict[job])
            else:
                nameSyst = theSyst
            hist.SetName('%s%s%s' %(Dict[job],nameSyst,Q))
            hist.Write()
            rooDataHist = ROOT.RooDataHist('%s%s%s' %(Dict[job],nameSyst,Q),'%s%s%s'%(Dict[job],nameSyst,Q),obs, hist)
            getattr(WS,'import')(rooDataHist)

if toy or signal_inject: 
    hDummy.SetName('data_obs')
    hDummy.Write()
    rooDataHist = ROOT.RooDataHist('data_obs','data_obs',obs, hDummy)
else:
    theData.SetName('data_obs')
    theData.Write()
    rooDataHist = ROOT.RooDataHist('data_obs','data_obs',obs, theData)

getattr(WS,'import')(rooDataHist)

WS.writeToFile(outpath+'vhbb_WS_'+ROOToutname+'.root')

# now we have a Dict final_histos with sets of all grouped MCs for all systematics:
# nominal, ($SYS_Up/Down)*4, weightF_sys_Up/Down, stats_Up/Down

print '\n\t >>> PRINTOUT PRETTY TABLE <<<\n'
#header
printout = ''
printout += '%-25s'%'Process'
printout += ':'
for item, val in final_histos['nominal'].items():
    printout += '%-12s'%item
print printout+'\n'
for key in final_histos:
    printout = ''
    printout += '%-25s'%key
    printout += ':'
    for item, val in final_histos[key].items():
        printout += '%-12s'%str('%0.5f'%val.Integral())
    print printout

#-----------------------------------------------------------------------------------------------------------

# -------------------- write DATAcard: ----------------------------------------------------------------------
DCprocessseparatordict = {'WS':':','TH':'/'}
# create two datacards: for TH an WS
for DCtype in ['WS','TH']:
    columns=len(setup)
    fileName = outpath+'vhbb_DC_%s_%s.txt'%(DCtype,ROOToutname)
    f = open(fileName,'w')
    f.write('imax\t1\tnumber of channels\n')
    f.write('jmax\t%s\tnumber of backgrounds (\'*\' = automatic)\n'%(columns-1))
    f.write('kmax\t*\tnumber of nuisance parameters (sources of systematical uncertainties)\n\n')
    f.write('shapes * * vhbb_%s_%s.root $CHANNEL%s$PROCESS $CHANNEL%s$PROCESS$SYSTEMATIC\n\n'%(DCtype,ROOToutname,DCprocessseparatordict[DCtype],DCprocessseparatordict[DCtype]))
    f.write('bin\t%s\n\n'%Datacardbin)
    if toy or signal_inject:
        f.write('observation\t%s\n\n'%(hDummy.Integral()))
    else:
        f.write('observation\t%s\n\n'%(theData.Integral()))
    # datacard bin
    f.write('bin\t')
    for c in range(0,columns): f.write('\t%s'%Datacardbin)
    f.write('\n')
    # datacard process
    f.write('process\t')
    for c in setup: f.write('\t%s'%Dict[c])
    f.write('\n')
    f.write('process\t')
    for c in range(0,columns): f.write('\t%s'%(c-len(signals)+1))
    f.write('\n')
    # datacard yields
    f.write('rate\t')
    print "workspace_datacard-setup: ", setup
    print "workspace_datacard-final_histos: ", final_histos
    for c in setup: 
        f.write('\t%s'%final_histos['nominal'][c].Integral())
    f.write('\n')
    # get list of systematics in use
    InUse=eval(config.get('Datacard','InUse_%s_%s'%(str(anType), pt_region)))
    # write non-shape systematics
    for item in InUse:
        f.write(item)
        what=eval(config.get('Datacard',item))
        f.write('\t%s'%what['type'])
        for c in setup:
            if c in what:
                if '_eff_e' in item and 'Zmm' in data_sample_names: f.write('\t-')
                elif '_eff_m' in item and 'Zee' in data_sample_names: f.write('\t-')
                elif '_trigger_e' in item and 'Zmm' in data_sample_names: f.write('\t-')
                elif '_trigger_m' in item and 'Zee' in data_sample_names: f.write('\t-')
                else:
                    f.write('\t%s'%what[c])
            else:
                f.write('\t-')
        f.write('\n')
    if not ignore_stats:
    # Write statistical shape variations
        if binstat:
            for c in setup:
                for bin in range(0,nBins):
                    if bin in binsBelowThreshold[c]:
                        f.write('%s_bin%s_%s_%s\tshape'%(systematicsnaming['stats'],bin,Dict[c],Datacardbin))
                        for it in range(0,columns):
                            if it == setup.index(c):
                                f.write('\t1.0')
                            else:
                                f.write('\t-')
                        f.write('\n')
        else:
            for c in setup:
                f.write('%s_%s_%s\tshape'%(systematicsnaming['stats'],Dict[c],Datacardbin))
                for it in range(0,columns):
                    if it == setup.index(c):
                        f.write('\t1.0')
                    else:
                        f.write('\t-')
                f.write('\n')
    # UEPS systematics
    for weightF_sys in weightF_systematics:
        f.write('%s\tshape' %(systematicsnaming[weightF_sys]))
        for it in range(0,columns): f.write('\t1.0')
        f.write('\n')
    # additional sample systematics
    if addSample_sys:
        alreadyAdded = []
        for newSample in addSample_sys.iterkeys():
            for c in setup:
                if not c == GroupDict[newSample]: continue
                if Dict[c] in alreadyAdded: continue
                f.write('%s_%s\tshape'%(systematicsnaming['model'],Dict[c]))
                for it in range(0,columns):
                    if it == setup.index(c):
                         f.write('\t1.0')
                    else:
                         f.write('\t-')
                f.write('\n')
                alreadyAdded.append(Dict[c])
    # regular systematics
    for sys in systematics:
        sys_factor=sys_factor_dict[sys]
        f.write('%s\tshape'%systematicsnaming[sys])
        for c in setup:
            if c in sys_affecting[sys] or 'all' in sys_affecting[sys]:
                f.write('\t%s'%sys_factor)
            else:
                f.write('\t-')
        f.write('\n')
    # write rateParams systematics (free parameters)

    rateParams=eval(config.get('Datacard','rateParams_%s_%s'%(str(anType), pt_region)))
    for rateParam in rateParams:
        dictProcs=eval(config.get('Datacard',rateParam))
        for proc in dictProcs.keys():
            f.write(rateParam+'\trateParam\t'+Datacardbin+'\t'+proc+'\t'+str(dictProcs[proc])+'\n')

    f.close()
    useSpacesInDC(fileName)

# --------------------------------------------------------------------------




outfile.Close()
