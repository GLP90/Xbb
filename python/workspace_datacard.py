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
import zlib
import base64
import re


def useSpacesInDC(fileName):
    print 'useSpacesInDC'
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
parser.add_option("-O", "--optimisation", dest="optimisation", default="",#not used for the moment
                      help="variable for shape when optimising the BDT")
parser.add_option("-s", "--settings", dest="settings", default=False,
                              help="contains target sample for the splitsubcaching")
parser.add_option("-m", "--mergeplot", dest="mergeplot", default=False,
                              help="option to merge")
#parser.add_option("-M", "--mergecachingplot", dest="mergecachingplot", default=False, action='store_true', help="use files from mergecaching")
parser.add_option("-M", "--mergecachingplot", dest="mergecachingplot", default=False, help="use files from mergecaching")
parser.add_option("-f", "--filelist", dest="filelist", default="",
                              help="list of files you want to run on")
#parser.add_option("-R", "--return_cut_string", dest="return_cut_string", default=False,
#                              help="Compute the caching cutstring (correspondings to SYS1_Up/Down || SYS2_Up/Down || ...), returns it and stop. Used to check is mergesyscaching needs to be submited to specific sample")

(opts, args) = parser.parse_args(argv)
config = BetterConfigParser()
print 'opts.config is', opts.config
config.read(opts.config)
var=opts.variable

# to avoid argument size limits, filelist can be encoded with 'base64:' + base64(zlib(.)), decode it first in this case
if opts.filelist.startswith('base64:'):
    opts.filelist = zlib.decompress(base64.b64decode(opts.filelist[7:]))
    #print 'zlib decoded file list:', opts.filelist

filelist=filter(None,opts.filelist.replace(' ', '').split(';'))
# print filelist
print "len(filelist)",len(filelist),
if len(filelist)>0:
    print "filelist[0]:",filelist[0];
else:
    print ''
print 'mergecachingplot is', opts.mergecachingplot

#Parsing doesn't work for some reason...
#opts.mergecachingplot = True
#opts.mergecachingplot = False


#-------------------------------------------------------------------------------

#--read variables from config---------------------------------------------------
# 7 or 8TeV Analysis

print "Compile external macros"
print "=======================\n"

if os.path.exists("../interface/DrawFunctions_C.so"):
    print 'ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")'
    ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")
if os.path.exists("../interface/VHbbNameSpace_h.so"):
    print 'ROOT.gROOT.LoadMacro("../interface/VHbbNameSpace_h.so")'
    ROOT.gROOT.LoadMacro("../interface/VHbbNameSpace_h.so")

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
optimisation=opts.optimisation
optimisation_training = False
UseTrainSample = eval(config.get('Analysis','UseTrainSample'))
if UseTrainSample:
    print 'Training events will be used'
if not optimisation == '':
    print 'Preparing DC for BDT optimisaiton'
    optimisation_training = True
print 'optimisation is', optimisation
try:
    os.stat(outpath)
except:
    os.mkdir(outpath)
# parse histogram config:
treevar = config.get('dc:%s'%var,'var')
print 'treevar is', treevar
name = config.get('dc:%s'%var,'wsVarName')
if optimisation_training:
    treevar = optimisation+'.Nominal'
    name += '_'+ optimisation
    if UseTrainSample:
        name += '_Train'
print 'again, treevar is', treevar
title = name
# set binning
nBins = int(config.get('dc:%s'%var,'range').split(',')[0])
xMin = float(config.get('dc:%s'%var,'range').split(',')[1])
xMax = float(config.get('dc:%s'%var,'range').split(',')[2])
print 'nBins is', nBins
print 'xMin is', xMin
print 'xMax is', xMax
ROOToutname = config.get('dc:%s'%var,'dcName')
RCut = config.get('dc:%s'%var,'cut')
signals = eval('['+config.get('dc:%s'%var,'signal')+']')
datas = config.get('dc:%s'%var,'dcBin')
Datacardbin=config.get('dc:%s'%var,'dcBin')
anType = config.get('dc:%s'%var,'type')
setup=eval(config.get('LimitGeneral','setup'))

#new
try:
    BDTmin = eval(config.get('LimitGeneral', 'BDTmin'))
except:
    BDTmin = None
#old
#Custom_BDT_bins = eval(config.get('LimitGeneral','Custom_BDT_bins'))

if optimisation_training:
   ROOToutname += optimisation
   if UseTrainSample:
       ROOToutname += '_Train'


keep_branches = eval(config.get('Branches', 'keep_branches'))

import os
if os.path.exists("$CMSSW_BASE/src/Xbb/interface/DrawFunctions_C.so"):
    print 'ROOT.gROOT.LoadMacro("$CMSSW_BASE/src/Xbb/interface/DrawFunctions_C.so")'
    ROOT.gROOT.LoadMacro("$CMSSW_BASE/src/Xbb/interface/DrawFunctions_C.so")

if os.path.exists("$CMSSW_BASE/src/Xbb/interface/VHbbNameSpace_h.so"):
    print 'ROOT.gROOT.LoadMacro("$CMSSW_BASE/src/Xbb/interface/VHbbNameSpace_h.so")'
    ROOT.gROOT.LoadMacro("$CMSSW_BASE/src/Xbb/interface/VHbbNameSpace_h.so")

###

print 'opts.settings is', opts.settings
sample_to_merge_ = None
# reads n files, writes single file. disabled if set to -1
mergeCachingPart = -1
split = False
merge = False
if opts.settings:
    if 'CACHING' in opts.settings:
        sample_to_merge_ = '__'.join(opts.settings[opts.settings.find('CACHING')+7:].split('__')[1:])
        print '@INFO: Only caching will be performed. The sample to be cached is', sample_to_merge_
    #if 'CACHING' in opts.settings:
    #    sample_to_merge_ = opts.settings[opts.settings.find('CACHING')+7:].split('__')[1]
    #    print '@INFO: Only caching will be performed. The sample to be cached is', sample_to_merge_
    #    print 'sample_to_merge is', sample_to_merge_
    if 'MERGECACHING' in opts.settings:
        mergeCachingPart = int(opts.settings[opts.settings.find('CACHING')+7:].split('__')[0].split('_')[-1])
        print '@INFO: Partially merged caching: this is part', mergeCachingPart
    if 'SPLIT' in opts.settings:
        split_number = int(opts.settings[opts.settings.find('SPLIT')+5:].split('__')[0].split('_')[-1])
        print '@INFO: goind to split the dc step. The split number of this job is', split_number
        split = True
    if 'DCMERGE' in opts.settings:
        print '@INFO: going to merge all the files produced during the split step'
        merge = True
    #if 'SPLITSAMPLE' in opts.settings:
    #    splitSample= int(opts.settings[opts.settings.find('CACHING')+11:].split('__')[0].split('_')[-1])
    #    print '@INFO: will only do the dc step for the following sample', mergeCachingPart


###
#sys.exit()

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
additionals = []

#Not sure what is the use of this variable
addSample_sys = False
#if config.has_option('LimitGeneral','addSample_sys'):
#    addSample_sys = eval(config.get('LimitGeneral','addSample_sys'))
#    additionals = [addSample_sys[key] for key in addSample_sys]
#else:
#    addSample_sys = None
#    additionals = []
#find out if BDT or MJJ:
bdt = False
mjj = False
cr = False
#lhe_muF = []
#lhe_muR = []
if str(anType) == 'BDT':
    bdt = True
    systematics = eval(config.get('LimitGeneral','sys_BDT'))
#    if config.has_option('LimitGeneral','sys_lhe_muF_BDT'): lhe_muF = eval(config.get('LimitGeneral','sys_lhe_muF_BDT'))
#    if config.has_option('LimitGeneral','sys_lhe_muR_BDT'): lhe_muR = eval(config.get('LimitGeneral','sys_lhe_muR_BDT'))
elif str(anType) == 'Mjj' or str(anType) == 'mjj':
    mjj = True
    systematics = eval(config.get('LimitGeneral','sys_Mjj'))
#    if config.has_option('LimitGeneral','sys_lhe_muF_Mjj'): lhe_muF = eval(config.get('LimitGeneral','sys_lhe_muF_Mjj'))
#    if config.has_option('LimitGeneral','sys_lhe_muR_Mjj'): lhe_muR = eval(config.get('LimitGeneral','sys_lhe_muR_Mjj'))
elif str(anType) == 'cr':
    cr = True
    systematics = eval(config.get('LimitGeneral','sys_cr'))
#    if config.has_option('LimitGeneral','sys_lhe_muF_cr'): lhe_muF = eval(config.get('LimitGeneral','sys_lhe_muF_cr'))
#    if config.has_option('LimitGeneral','sys_lhe_muR_cr'): lhe_muR = eval(config.get('LimitGeneral','sys_lhe_muR_cr'))
else:
    print 'EXIT: please specify if your datacards are BDT, Mjj or cr.'
    sys.exit()

sys_cut_suffix=eval(config.get('LimitGeneral','sys_cut_suffix'))
sys_weight_corr=eval(config.get('LimitGeneral','sys_weight_corr'))
#exclude_sys_weight = eval(config.get('LimitGeneral','exclude_sys_weight'))
decorrelate_sys_weight = eval(config.get('LimitGeneral','decorrelate_sys_weight'))
sys_cut_include=[]
if config.has_option('LimitGeneral','sys_cut_include'):
    sys_cut_include=eval(config.get('LimitGeneral','sys_cut_include'))
sys_factor_dict = eval(config.get('LimitGeneral','sys_factor'))
sys_affecting = eval(config.get('LimitGeneral','sys_affecting'))
sys_lhe_affecting = {}
if config.has_option('LimitGeneral','sys_lhe_affecting'): sys_lhe_affecting = eval(config.get('LimitGeneral','sys_lhe_affecting'))

# weightF:
weightF = config.get('Weights','weightF')
SBweight = None
print 'before adding SBweight, weightF is',  weightF
if mjj:
    print 'Passed mJJ'
    if config.has_option('dc:%s'%var,'SBweight'):
        print 'passed config'
        SBweight = config.get('dc:%s'%var,'SBweight')
        weightF ='('+weightF+')*('+SBweight+')'
        print 'after adding SBweight, weightF is',  weightF
    else:
        print 'NOT Passed config'

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
#backgrounds = eval(config.get('LimitGeneral','BKG'))
#Groups for adding samples together
GroupDict = eval(config.get('LimitGeneral','Group'))
#naming for DC
Dict= eval(config.get('LimitGeneral','Dict'))
#treating statistics bin-by-bin:
binstat = eval(config.get('LimitGeneral','binstat'))

#no bb for CR
if str(anType) == 'cr':
    binstat = False

# Use the rebinning:
rebin_active=eval(config.get('LimitGeneral','rebin_active'))
#if str(anType) == 'cr':
print 'rebin active is', rebin_active
if not bdt:
    if rebin_active:
        print '@WARNING: Changing rebin_active to false since you are running for control region.'
    rebin_active = False
# ignore stat shapes
ignore_stats = eval(config.get('LimitGeneral','ignore_stats'))
#max_rel = float(config.get('LimitGeneral','rebin_max_rel'))
signal_inject=eval(config.get('LimitGeneral','signal_inject'))
print 'signal_inject is',signal_inject
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
elif 'Mass' in ROOToutname:
    if 'Vptbin0' in ROOToutname:
        pt_region = 'bin0'
    if 'Vptbin1' in ROOToutname:
        pt_region = 'bin1'
    if 'Vptbin2' in ROOToutname:
        pt_region = 'bin2'
    if 'Vptbin150To200' in ROOToutname:
        pt_region = 'bin150To200'
    if 'Vptbin200ToInf' in ROOToutname:
        pt_region = 'bin200ToInf'
else:
    print "Unknown Pt region"
    pt_region = 'NoSysRegion'
    #sys.exit("Unknown Pt region")

print 'pt_region is', pt_region
systematicsnaming = eval(config.get('LimitGeneral','systematicsnaming'))
#systematicsnaming = eval(config.get('LimitGeneral','systematicsnaming_%s'%pt_region))
print 'systematicsnaming is', systematicsnaming
weightF_systematics = eval(config.get('LimitGeneral','weightF_sys'))
print 'ROOToutname is', ROOToutname
if 'Zee' in ROOToutname :
    for weight_ in copy(weightF_systematics):
        if weight_ == 'CMS_vhbb_eff_m_13TeV': weightF_systematics.remove('CMS_vhbb_eff_m_13TeV')
        if weight_ == 'CMS_vhbb_eff_m_trigger_Zll_13TeV': weightF_systematics.remove('CMS_vhbb_eff_m_trigger_Zll_13TeV')
        if weight_ == 'CMS_vhbb_eff_m_MVAID_Zll_13TeV': weightF_systematics.remove('CMS_vhbb_eff_m_MVAID_Zll_13TeV')
        if weight_ == 'CMS_vhbb_eff_m_tracker_Zll_13TeV': weightF_systematics.remove('CMS_vhbb_eff_m_tracker_Zll_13TeV')
        if weight_ == 'CMS_vhbb_eff_m_ISO_Zll_13TeV': weightF_systematics.remove('CMS_vhbb_eff_m_ISO_Zll_13TeV')

#    if '_m_' in weightF_systematics:
#        weightF_systematics.remove('CMS_vhbb_eff_m_13TeV')
#        weightF_systematics.remove('CMS_vhbb_eff_m_trigger_Zll_13TeV')
#        weightF_systematics.remove('CMS_vhbb_eff_m_MVAID_Zll_13TeV')
#        weightF_systematics.remove('CMS_vhbb_eff_m_tracker_Zll_13TeV')
#        weightF_systematics.remove('CMS_vhbb_eff_m_ISO_Zll_13TeV')
if 'Zuu' in ROOToutname :
    for weight_ in copy(weightF_systematics):
        if weight_ == 'CMS_vhbb_eff_e_13TeV': weightF_systematics.remove('CMS_vhbb_eff_e_13TeV')
        if weight_ == 'CMS_vhbb_eff_e_trigger_Zll_13TeV': weightF_systematics.remove('CMS_vhbb_eff_e_trigger_Zll_13TeV')
        if weight_ == 'CMS_vhbb_eff_e_MVAID_Zll_13TeV': weightF_systematics.remove('CMS_vhbb_eff_e_MVAID_Zll_13TeV')
        if weight_ == 'CMS_vhbb_eff_e_MVAID_Zll_eta0_13TeV': weightF_systematics.remove('CMS_vhbb_eff_e_MVAID_Zll_eta0_13TeV')
        if weight_ == 'CMS_vhbb_eff_e_MVAID_Zll_eta1_13TeV': weightF_systematics.remove('CMS_vhbb_eff_e_MVAID_Zll_eta1_13TeV')
        if weight_ == 'CMS_vhbb_eff_e_tracker_Zll_13TeV': weightF_systematics.remove('CMS_vhbb_eff_e_tracker_Zll_13TeV')
#    if if weight == ''_e_' in weightF_systematics:
#        weightF_systematics.remove('CMS_vhbb_eff_e_13TeV')
#        weightF_systematics.remove('CMS_vhbb_eff_e_trigger_Zll_13TeV')
#        weightF_systematics.remove('CMS_vhbb_eff_e_MVAID_Zll_13TeV')
#        weightF_systematics.remove('CMS_vhbb_eff_e_tracker_Zll_13TeV')

#print 'weightF_systematics are', weightF_systematics
#sys.exit()

#if str(anType) == 'cr': 
#    if pt_region == 'NoSysRegion':
#        weightF_systematics = eval(config.get('LimitGeneral','weightF_sys_CR'))
#    elif pt_region == 'HighPt':
#        weightF_systematics = eval(config.get('LimitGeneral','weightF_sys_CR_HighPt'))
#    elif pt_region == 'LowPt':
#        weightF_systematics = eval(config.get('LimitGeneral','weightF_sys_CR_LowPt'))
#elif str(anType) == 'BDT': 
#    if pt_region == 'NoSysRegion':
#        weightF_systematics = eval(config.get('LimitGeneral','weightF_sys_CR'))
#    elif pt_region == 'HighPt':
#        weightF_systematics = eval(config.get('LimitGeneral','weightF_sys_BDT_HighPt'))
#    elif pt_region == 'LowPt':
#        weightF_systematics = eval(config.get('LimitGeneral','weightF_sys_BDT_LowPt'))
#else: weightF_systematics = eval(config.get('LimitGeneral','weightF_sys'))
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
backgrounds = eval(config.get('dc:%s'%var,'background'))

sample_sys_info = {}
#Systematics from different sampe model (e.g. parton shower)
if config.has_option('LimitGeneral','sample_sys_info'):
    sample_sys_list = []#List of all the samples used for the sys. Those samples need to be skiped, except for corresponding sys
    sample_sys_info = eval(config.get('LimitGeneral','sample_sys_info'))
    #Extract list of sys samples
    for key, item in sample_sys_info.iteritems():
        for item2 in item:
            for sample_type in item2:
                NOMsamplesys = sample_type[0]
                noNom = False
                for nomsample in NOMsamplesys: #This is for mergesyscachingdcsplit. Doesn't add the sys if nom is not present
                    print 'nomsample is', nomsample
                    print 'signals+backgrounds are', signals+backgrounds
                    if nomsample not in signals+backgrounds: noNom = True
                if noNom: continue
                DOWNsamplesys = sample_type[1]
                UPsamplesys = sample_type[2]
                sample_sys_list += DOWNsamplesys
                sample_sys_list += UPsamplesys
#    additionals += sample_sys_list
else:
    sample_sys_list = []

additionals += sample_sys_list
print 'additioinals are', additionals

#Create dictonary to "turn of" all the sample systematic (for nominal)
sample_sys_dic = {}
for sample_sys in sample_sys_list:
    sample_sys_dic[sample_sys] = False

print 'sample_sys_dic is', sample_sys_dic

#sys.exit()

#How to split the MC background
split_factor = eval(config.get('LimitGeneral','split_factor'))
#split_factor = 0
#should go from 0 to split_factor+1. If split_number = split_factor+1, no MC is used for the computation but just the data
#split_number = 0

split_samples = []

MC_samples = signals+backgrounds+additionals

print 'Befor split selection, MC_samples are:', MC_samples

#only a fraction of the MC samples are computed


lastMCsample = False
if split and split_number == split_factor+2:
    lastMCsample = True

split_data = False
if split and split_number == split_factor+3:
    split_data = True


if split and not split_data:
    #compute how many samples should be added in the group
    NSamples = len(MC_samples)
    k = (NSamples - (NSamples%split_factor))/split_factor
    print 'k is', k
    counter_ = 0
    for sample_ in MC_samples[split_number*k:]:
        counter_ +=1
        if counter_ > k and not lastMCsample : break
        split_samples.append(sample_)
    MC_samples = split_samples

if split and split_data:
    MC_samples = []

print 'MC_samples are', MC_samples


#all_samples = info.get_samples(signals+backgrounds+additionals)
#To prepare Histomaker
all_samples_HM = info.get_samples(signals+backgrounds+additionals)
all_samples = info.get_samples(MC_samples)
print 'workspace_datacard-all_samples:',[job.name for job in all_samples]

signal_samples = info.get_samples(signals) 
print 'signal samples:',[job.name for job in signal_samples]

background_samples = info.get_samples(backgrounds) 

data_sample_names = eval(config.get('dc:%s'%var,'data'))


print 'data_sample_names are', data_sample_names


data_samples = info.get_samples(data_sample_names)

if split  and not split_data:
    data_samples = []
elif split:
    print '@INFO: this split job is taking care of the data'

#split_data = False
#if split and split_number != split_factor+3:
#    data_samples = []
#elif split:
#    print '@INFO: this split job is taking care of the data'
#    split_data = True


print 'data_samples are', data_samples

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

#clean setup to contain only samples from split
setup_copy = copy(setup)
print 'before cleaning, setup is', setup_copy
if split:
    for c in setup:
        found = False
        for mc_sample in all_samples:
#            print 'sample name is', mc_sample.name
#            print 'corresponding dic is', GroupDict[mc_sample.name]
            if GroupDict[mc_sample.name] == c:
                found = True
                break
        if not found: setup_copy.remove(c)
    setup = setup_copy
#print 'after cleaning, setup is', setup
#sys.exit()
#-------------------------------------------------------------------------------------------------

optionsList=[]
shapecutList=[]

def appendList(): optionsList.append({'cut':copy(_cut),'var':copy(_treevar),'name':copy(_name),'nBins':nBins,'xMin':xMin,'xMax':xMax,'weight':copy(_weight),'countHisto':copy(_countHisto),'countbin':copy(_countbin),'blind':blind, 'sysType':copy(_sysType),'SBweight':copy(SBweight),'sample_sys_dic':copy(_sample_sys_dic)})
def appendSCList(): shapecutList.append(shapecut)

#nominal
_cut = treecut
_treevar = treevar
_name = title
_weight = weightF
_countHisto = "CountWeighted"
_countbin = 0
_sysType = 'nominal'
_sample_sys_dic = sample_sys_dic

#shapecut = _cut
#ie. take count from 'CountWeighted->GetBinContent(1)'
appendList()
#appendSCList()

print "Using weightF:",weightF
print 'Assign the systematics'
print '======================\n'

import os
if os.path.exists("$CMSSW_BASE/src/Xbb/interface/DrawFunctions_C.so"):
    print 'ROOT.gROOT.LoadMacro("$CMSSW_BASE/src/Xbb/interface/DrawFunctions_C.so")'
    ROOT.gROOT.LoadMacro("$CMSSW_BASE/src/Xbb/interface/DrawFunctions_C.so")

#all the cuts except the one modified by the shape variation
shapecut= ''
cutlist =  _cut.split('&')
rmv_sys = _cut.split('&')
sysnomcut = ''
print 'cutlist is ', cutlist

#shape systematics
for syst in systematics:
    for Q in UD:
        #print 'Q is', Q
        _cut = treecut
        _name = title
        _weight = weightF
        _sample_sys_dic = sample_sys_dic
        #if not 'UD' in syst:
        if not isinstance(sys_cut_suffix[syst], list):
            new_cut=sys_cut_suffix[syst]
            if not new_cut == 'nominal':
                old_str,new_str=new_cut.split('>')
                _cut = treecut.replace(old_str,new_str.replace('?',Q))
                _name = title
                _weight = weightF
                for c_ in cutlist:
                    if (old_str in c_) and (c_ in rmv_sys): rmv_sys.remove(c_)
        else:
            new_cut_list=sys_cut_suffix[syst]
            for new_cut in new_cut_list:
                old_str,new_str=new_cut.split('>')
                _cut = _cut.replace(old_str,new_str.replace('SYS',syst).replace('UD',Q))
                for c_ in cutlist:
                    if (old_str in c_) and (c_ in rmv_sys): rmv_sys.remove(c_)
            _name = title
            _weight = weightF
        print ''


        if syst in sys_weight_corr:
            print 'sys_weight is',sys_weight_corr[syst]+'_%s' %(Q.upper())
            _weight = config.get('Weights',sys_weight_corr[syst]+'_%s' %(Q.upper()))
            print '_weight is', _weight
        #replace tree variable
        if bdt == True:
            if not 'UD' in syst:
                print 'treevar was', _treevar
                #ver3
                _treevar = treevar.replace('.Nominal','.%s_%s'%(syst,Q))
                print '.nominal by','.%s_%s'%(syst,Q)
            else:
                _treevar = treevar.replace('.nominal','.%s'%(syst.replace('UD',Q)))
                print '.nominal by','.%s'%(syst.replace('UD',Q))
            #print 'treevar after replacement', _treevar
        elif mjj == True:
            if not 'UD' in syst:
                print 'treevar was', _treevar
                _treevar = treevar.replace('_reg_mass','_reg_mass_corr%s%s'%(syst,Q))
                print '_reg_mass','_reg_mass_corr%s%s'%(syst,Q)
            else:
                print '@ERROR: Why is there UD in sys ? Abort'
                sys.exit()
                #_treevar = treevar.replace('_reg_mass','%s'%(syst.replace('UD',Q)))

            #    _treevar = treevar.replace('_reg_mass','_reg_corrJER%s_mass'%Q)
            #elif syst == 'JES':
            #    _treevar = treevar.replace('_reg_mass','_reg_corrJEC%s_mass'%Q)
            #else:
            #    _treevar = treevar
        elif cr == True:
            _treevar = treevar

        _sysType = 'shape'
        #append
        appendList()
        #appendSCList()
        #print 'new tree cut is', _cut

#rmv_sys are all the cut NOT affected by the shape sys
print 'rmv_sys is', rmv_sys
shapecut_first = ''
for opt in optionsList:
    cutlist =  opt['cut'].split('&')
    #print 'rmv_sys is', rmv_sys
    #print 'again, cutlist is', cutlist
    for rsys in rmv_sys:
        #print 'rsys is', rsys
        for c_ in cutlist:
            if (rsys == c_):
                #print 'rsys will be removes'
                nbra = c_.count('(')
                nket = c_.count(')')
                if nbra > nket:
                    newc_ = abs(nbra-nket)*'('+'1'
                    cutlist[cutlist.index(c_)] = newc_
                elif nket > nbra:
                    newc_ = '1'+ abs(nbra-nket)*')'
                    cutlist[cutlist.index(c_)] = newc_
                elif nket ==  nbra:
                    cutlist.remove(c_)

    shapecut = '&'.join(cutlist)
    if opt == optionsList[0]:
        shapecut_first = shapecut
    #    shapecut = opt['cut']
    #    #shapecut = sysnomcut
    appendSCList()

#to avoid parsing errors
for rmv_ in rmv_sys:
    index_ =  rmv_sys.index(rmv_)
    nbra = rmv_.count('(')
    nket = rmv_.count(')')
    if nbra > nket:
        rmv_ = rmv_ + abs(nbra-nket)*')'
    elif nket > nbra:
        rmv_ = abs(nbra-nket)*'('+rmv_
    rmv_sys[index_] = rmv_

sysnomcut = '&'.join(rmv_sys)

print 'after removing shape sys'
print 'shapecut', shapecut #not needed anymore
print 'shapecut_first', shapecut_first #contains only cut variable affected by shape (not weight sys). Nominal case
print 'sysnomcut', sysnomcut #this is the cut string without the sys variables
#appendSCList()
#sys.exit(0)


replace_cut =eval(config.get('LimitGeneral','replace_cut'))
#make optimised shapecut
shapecut_split = shapecut_first.split('&')
for shape__ in shapecut_split:
    if shape__.replace(' ','')  == '': continue#to avoid && case
    shapecut_split_ = shape__.split('||')
    for shape_ in  shapecut_split_:
        #new_cut_list=sys_cut_suffix[syst]
        for new_cut in replace_cut:
            old_str,new_str=new_cut.split('>')
            if old_str in shape_:
                print 'when removing everything, string is', shape_.replace('>','').replace('<','').replace(' ','').replace('(','').replace(')','').replace('||','').replace(old_str,'')
                try:
                    float(shape_.replace('>','').replace('<','').replace(' ','').replace('(','').replace(')','').replace('||','').replace(old_str,''))
                except:
                    newcut_ = '((%s) || (%s))'%(shape_.replace(old_str,new_str.replace('SYS','_').replace('UD','Min')),shape_.replace(old_str,new_str.replace('SYS','_').replace('UD','Max')))
                    #duplication of cut will also duplicate addtional ( or ). closing here
                    nbra = shape_.count('(')
                    nket = shape_.count(')')
                    if nbra > nket:
                        newcut_   = newcut_ + abs(nbra-nket)*')'
                    elif nket > nbra:
                        newcut_   = abs(nbra-nket)*'('+newcut_
                    print 'newcut_ is ', newcut_
                    shapecut_split_[shapecut_split_.index(shape_)] = newcut_
                    continue
                if shape_.split(old_str)[0].replace(' ','').replace('(','').replace(')','').endswith('>') or shape_.split(old_str)[1].replace(' ','').replace('(','').replace(')','').startswith('<'):
                    shapecut_split_[shapecut_split_.index(shape_)] = shape_.replace(old_str,new_str.replace('SYS','_').replace('UD','Min'))
                    continue
                elif shape_.split(old_str)[0].replace(' ','').replace('(','').replace(')','').endswith('<') or shape_.split(old_str)[1].replace(' ','').replace('(','').replace(')','').startswith('>'):
                    shapecut_split_[shapecut_split_.index(shape_)] = shape_.replace(old_str,new_str.replace('SYS','_').replace('UD','Max'))
                    continue
                print '@ERROR: cut strings could be parsed correctly'
                print 'Aborting'
                sys.exit()

    shapecut_split[shapecut_split.index(shape__)] = '||'.join(shapecut_split_)
shapecut_MinMax = '&'.join(shapecut_split)

        #_cut = _cut.replace(old_str,new_str.replace('SYS',syst).replace('UD',Q))

#shapecut_MinMax = '&'.join(shapecut_split)
#print 'shapecut_MinMax is', shapecut_MinMax

dccut = sysnomcut + '&(' + shapecut_MinMax + ')'
dccutdata = sysnomcut + '&(' + shapecut_first + ')'
print 'dccut is', dccut
print 'dccutdata is', dccutdata

#sys.exit()

#UEPS
#Appends options for each weight 
for weightF_sys in weightF_systematics:
    #if '_eff_e' in weightF_sys and 'Zuu' in ROOToutname : continue
    #if '_eff_m' in weightF_sys and 'Zee' in ROOToutname : continue
    for _weight in [config.get('Weights','%s_UP' %(weightF_sys)),config.get('Weights','%s_DOWN' %(weightF_sys))]:
        #_cut = treecut
        #shapecut = sysnomcut
        #_cut = "1"
        #shapecut = "1"
        if not SBweight == None:
            _weight ='('+_weight+')*('+SBweight+')'
        _cut = shapecut_first
        shapecut = shapecut_first
        _treevar = treevar
        _name = title
        _sysType = 'weight'
        _sample_sys_dic = sample_sys_dic
        appendList()
        appendSCList()

#sample systematics
print 'before modif, _sample_sys_dic is', _sample_sys_dic
if len(sample_sys_info) > 0:
    for key, item in sample_sys_info.iteritems():#loop over the systematics
        _weight = weightF
        _cut = shapecut_first
        shapecut = shapecut_first
        _treevar = treevar
        _name = title
        _sysType = 'sample'
        #define up and down dictionary
        _sample_sys_dic_up = copy(sample_sys_dic)
        _sample_sys_dic_down = copy(sample_sys_dic)
        for item2 in item:#loop over list of sample per systematic e.g.: ggZH, ZH. Note: sample sys assumed to be correlated among the samples
            for sample_type in item2:
                NOMsamplesys  = sample_type[0]
                DOWNsamplesys = sample_type[1]
                UPsamplesys   = sample_type[2]
                #Set all the nominal sample to False
                for noms in NOMsamplesys:
                    _sample_sys_dic_up[noms] =  False
                    _sample_sys_dic_down[noms] =  False
                #prepare disctionnary for Up and Down variation
                for upsample, downsample in zip(UPsamplesys, DOWNsamplesys):
                    #Up variation
                    _sample_sys_dic_up[upsample] = True
                    _sample_sys_dic_up[downsample] = False
                    #appendList()
                    #appendSCList()
                    _sample_sys_dic_down[upsample] = False
                    _sample_sys_dic_down[downsample] = True
                    #appendList()
                    #appendSCList()
                    #reset to default
                 #_sample_sys_dic = sample_sys_dic

    #Fill optionsList
    #Up
    _sample_sys_dic = _sample_sys_dic_up
    appendList()
    appendSCList()
    #Down
    _sample_sys_dic = _sample_sys_dic_down
    appendList()
    appendSCList()


#print 'optionsList is', optionsList

##lhe_muF
##Appends options for each weight (up/down -> len =2 )
#if len(lhe_muF)==2:
#    for lhe_muF_num in lhe_muF:
#        _weight = weightF + "*LHE_weights_scale_wgt[%s]"%lhe_muF_num
#        #_cut = treecut
#        #shapecut = sysnomcut
#        _cut = "1"
#        shapecut = "1"
#        _treevar = treevar
#        _name = title
#        _countHisto = "CountWeightedLHEWeightScale"
#        _countbin = lhe_muF_num
#        appendList()
#        appendSCList()
#
#if len(lhe_muR)==2:
#    for lhe_muR_num in lhe_muR:
#        _weight = weightF + "*LHE_weights_scale_wgt[%s]"%lhe_muR_num
#        #_cut = treecut
#        #shapecut = sysnomcut
#        _cut = "1"
#        shapecut = "1"
#        _treevar = treevar
#        _name = title
#        _countHisto = "CountWeightedLHEWeightScale"
#        _countbin = lhe_muR_num
#        appendList()
#        appendSCList()

if len(optionsList) != len(shapecutList):
    print '@ERROR: optionsList and shapecutList don\'t have equal size. Aborting'
    sys.exit()

print '=================='
print 'all sample_sys_dic are:'
print '=================='
for op in optionsList:
    print 'sysType:', op['sysType'], 'sample_sys_dic:', op['sample_sys_dic'], '\n'
print ''

_countHisto = "CountWeighted"
_countbin = 0

print '===================\n'
print 'comparing cut strings'
for optold, optnew in zip(optionsList,shapecutList):
    #print 'old option is', optold['cut']
    #print 'new option is', optnew
    optionsList[optionsList.index(optold)]['cut']=optnew

############
#List the branches to keep here
############

def MakeBranchList(mystring):
    '''Takes a string as input (should be a cut/weigt/variable expression) and returns a list containing all the corresponding branches'''
    mylist = []
    def isfloat(value):
        try:
            float(value)
            return True
        except ValueError:
            return False
    mystring = mystring.replace('[','??').replace(']','??').replace('*','??').replace('(','??').replace(')','??').replace('||','??').replace('<','??').replace('>','??').replace('=','??').replace('.','??').replace('&','??').replace('+','??').replace('-','??').replace(',','??').replace(' ','')
    mystring_list = mystring.split('??')
    #remove '' and flaot from list
    for l in mystring_list:
        if (l == '' or isfloat(l)): continue
        mylist.append(l)

    return mylist

list_weights_ =  []
list_cuts_ =  []
list_cuts_.append(MakeBranchList(dccut))
list_cuts_.append(MakeBranchList(dccutdata))
list_var_ =  []
list_alwayskeep = []

for opt in optionsList:
    #weights
    list_weights_.append(MakeBranchList(opt['weight']))
    list_cuts_.append(MakeBranchList(opt['cut']))
    list_var_.append(MakeBranchList(opt['var']))

list_weights =  []
list_cuts =  []
list_var =  []

for l1 in list_weights_:
    for l2 in l1:
        list_weights.append(l2)
for l1 in list_cuts_:
    for l2 in l1:
        list_cuts.append(l2)
for l1 in list_var_:
    for l2 in l1:
        list_var.append(l2)

#print 'weights to keep are', list_weights
#print 'cuts to keep are', list_cuts
#print 'vars to keep are', list_var
#print 'keep_branches are', keep_branches

list_weights = list(set(list_weights))
list_cuts = list(set(list_cuts))
list_var = list(set(list_var))

#print 'weights to keep are', list_weights
#print 'cuts to keep are', list_cuts
#print 'vars to keep are', list_var
#print 'keep_branches are', keep_branches
#
#all_keep_list = list_weights+list_cuts+list_var+keep_branches
all_keep_list = None
print 'all branches to keep are', all_keep_list
#print 'length is', len(all_keep_list)
#sys.exit()

if split:

    print 'Check if split dc was already performed'
    print '=========================================\n'

    DCtype = 'TH'
    dc_dir = outpath+'vhbb_TH_'+ROOToutname
    if not os.path.exists(dc_dir):
        os.makedirs(dc_dir)

    if os.path.exists(dc_dir+'/'+ROOToutname+'_%i.root'%split_number):
        print 'The .root file has already been produced for this dc. Aborting'
        sys.exit()

print 'Preparations for Histograms (HistoMakeri)'
print '=========================================\n'

#merge = True
all_histos = {}
data_histos = {}
final_histos_merge = {}
if merge:
    #print 'Will merge the split dc'

    print 'Get the data histo'
    print '==================\n'

    #data_histos = {}

    #GroupDic = {}
    #hTreeList = []

    #Browse all the root files in the directory
    DCtype = 'TH'
    dc_dir = outpath+'vhbb_TH_'+ROOToutname
    if not os.path.exists(dc_dir):
        print '@ERROR: the directory were dc .root file are stored doesn t exist. Aborting'
        print 'The path is', outpath+'vhbb_TH_'+ROOToutname

    AllHisoDic = {}
    #Read all the root files and save histo in dic
    for root, dirs, filenames in os.walk(dc_dir):
        for f in filenames:
            no_ducplicates = []
            if '.root' in f:
                print 'root file is', f
                split_file = ROOT.TFile(dc_dir+'/'+f)
                split_file.cd(Datacardbin)
                hist_list = ROOT.gDirectory.GetListOfKeys()
                #print 'List of keys is'
                #hist_list.ls()
                #sys.exit()

                for hist in hist_list:
                    hname = hist.GetName()
                    if not hname in no_ducplicates:
                        no_ducplicates.append(hname)
                    else: continue

                    htree = copy(ROOT.gDirectory.Get(hname))
                    print 'hname is', hname
                    if hname in AllHisoDic:
                        AllHisoDic[hname].Add(htree)
                    else:
                        AllHisoDic[hname] = htree
    print 'AllHisoDic is', AllHisoDic

    #reorder the AllHisoDic in final_histos_merge
    Dict_inv = {v: k for k, v in Dict.items()}
    for key in AllHisoDic:

        if key.split('CMS')[0] == 'data_obs': continue
        sample_name = Dict_inv[key.split('CMS')[0]]
        if len(key.split('CMS')) == 2:
            sys_name = 'CMS'+key.split('CMS')[1]
        else:
            sys_name = 'nominal'
        if not sys_name in final_histos_merge:
            nuisDic = {}
            nuisDic[sample_name] = AllHisoDic[key]
            final_histos_merge[sys_name] = nuisDic
        else:
            final_histos_merge[sys_name][sample_name] = AllHisoDic[key]

    #print 'final_histos_merge is ', final_histos_merge

    ##Fill  hTreeListData
    #hTreeDicData = {}
    ##Fill hTreeList
    ##Nominal
    #hTreeDic = {}
    #for c in setup:
    #    hTreeDic[c] = AllHisoDic[Dict[c]]
    #hTreeList.append(hTreeDic)

    data_histos['DATA'] = AllHisoDic['data_obs']
    #for job in data_samples:
    #    print '\t- %s'%job
    #    data_histos[job.name] = AllHisoDic['data_obs']

else:
    print '================'
    print'mergeCachingPart is, ', mergeCachingPart
    print '================'

    mc_hMaker   = HistoMaker(samples=all_samples_HM,  path=path, config=config, optionsList=optionsList     , GroupDict=GroupDict, filelist=filelist, mergeplot=opts.mergeplot, sample_to_merge=sample_to_merge_, mergeCachingPart=mergeCachingPart, plotMergeCached = opts.mergecachingplot, branch_to_keep=all_keep_list, dccut = dccut)#sys should never be removed in dc
    data_hMaker = HistoMaker(samples=data_samples, path=path, config=config, optionsList=[optionsList[0]], GroupDict=None     , filelist=filelist, mergeplot=opts.mergeplot, sample_to_merge=sample_to_merge_, mergeCachingPart=mergeCachingPart, plotMergeCached = opts.mergecachingplot, branch_to_keep=all_keep_list, dccut = dccutdata)
    #
    #mc_hMaker   = HistoMaker(samples=all_samples,  path=path, config=config, optionsList=optionsList     , GroupDict=GroupDict, filelist=filelist, mergeplot=opts.mergeplot, sample_to_merge=sample_to_merge_, mergeCachingPart=mergeCachingPart, plotMergeCached = opts.mergecachingplot, branch_to_keep=all_keep_list, dccut = dccut)#sys should never be removed in dc
    #data_hMaker = HistoMaker(samples=data_samples, path=path, config=config, optionsList=[optionsList[0]], GroupDict=None     , filelist=filelist, mergeplot=opts.mergeplot, sample_to_merge=sample_to_merge_, mergeCachingPart=mergeCachingPart, plotMergeCached = opts.mergecachingplot, branch_to_keep=all_keep_list, dccut = dccutdata)
    ##before
    #mc_hMaker =   HistoMaker(all_samples ,path,config,optionsList     ,GroupDict, None, False, sample_to_merge_)
    #data_hMaker = HistoMaker(data_samples,path,config,[optionsList[0]], None    , None, False, sample_to_merge_)

    if sample_to_merge_ or opts.mergeplot:
        print "@INFO: Done splitcachingdc. Bye !"
        sys.exit()


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
        if BDTmin and str(anType) == 'BDT':
            mc_hMaker.BDTmin = BDTmin
        #old
        #if Custom_BDT_bins and str(anType) == 'BDT':
        #    mc_hMaker.Custom_BDT_bins = Custom_BDT_bins
        mc_hMaker.calc_rebin(background_samples, 1000, 0.35, True)
        #transfer rebinning info to data maker
        data_hMaker.norebin_nBins = copy(mc_hMaker.norebin_nBins)
        data_hMaker.rebin_nBins = copy(mc_hMaker.rebin_nBins)
        data_hMaker.nBins = copy(mc_hMaker.nBins)
        data_hMaker._rebin = copy(mc_hMaker._rebin)
        data_hMaker.mybinning = deepcopy(mc_hMaker.mybinning)

    #all_histos = {}
    #data_histos = {}

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
    #new
        #inputs.append((mc_hMaker,"get_histos_from_tree_dc",(job,True, None, shapecutList)))
    #old
        inputs.append((mc_hMaker,"get_histos_from_tree",(job,True, None, shapecutList)))


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
            outputs.append(getattr(input_[0],input_[1])(*input_[2])) #ie. mc_hMaker.get_histos_from_tree(job)

    print "job.name and all_histos[job.name]:"
    for i,job in enumerate(all_samples):
        all_histos[job.name] = outputs[i]


    print 'data_samples are', data_samples
    for job in data_samples:
        print '\t- %s'%job
        data_histos[job.name] = data_hMaker.get_histos_from_tree(job)[0]['DATA']

#sys.exit()

print '\t> done <\n'

print 'Get the bkg histo'
print '=================\n'
i=0
#?
#for job in background_samples:
#    print job.name
#    htree = all_histos[job.name][0].values()[0]
#    if not i:
#        hDummy = copy(htree)
#    else:
#        hDummy.Add(htree,1)
#    del htree
#    i+=1
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
#sys.exit()

#print 'Get the signal histo'
#print '====================\n'
#if signal_inject:
#    for job in signal_inject:
#        htree = sig_hMaker.get_histos_from_tree(job)
#        hDummy.Add(htree[0].values()[0],1)
#        del htree

print 'Get the data histo'
print '==================\n'
nData = 0
print 'data histos is', data_histos
for job in data_histos:
    if merge:
        theData = data_histos['DATA']
    else:
        if nData == 0:
            theData = data_histos[job]
            nData = 1
        else:
            theData.Add(data_histos[job])


print 'END DEBUG'


#-- Write Files-----------------------------------------------------------------------------------
# generate the TH outfile:

print 'Start writing the files'
print '=======================\n'

print 'Creating output file'
print '====================\n'

if split:
    dc_dir = outpath+'vhbb_TH_'+ROOToutname
    #if not os.path.exists(dc_dir):
    #    os.makedirs(dc_dir)

    #if os.path.exists(dc_dir+'/'+ROOToutname+'_%i.root'%split_number):
    #    print 'The .root file has already been produced for this dc. Aborting'
    #    sys.exit()
    outfile = ROOT.TFile(dc_dir+'/'+ROOToutname+'_%i.root'%split_number, 'RECREATE')
    outfile.mkdir(Datacardbin,Datacardbin)
    outfile.cd(Datacardbin)
    # generate the Workspace:
    #WS = ROOT.RooWorkspace('%s'%Datacardbin,'%s'%Datacardbin) #Zee
    #print 'WS initialized'
    disc= ROOT.RooRealVar(name,name,xMin,xMax)
    obs = ROOT.RooArgList(disc)
    #

else:
    outfile = ROOT.TFile(outpath+'vhbb_TH_'+ROOToutname+'.root', 'RECREATE')
    outfile.mkdir(Datacardbin,Datacardbin)
    outfile.cd(Datacardbin)
    # generate the Workspace:
    #WS = ROOT.RooWorkspace('%s'%Datacardbin,'%s'%Datacardbin) #Zee
    #print 'WS initialized'
    disc= ROOT.RooRealVar(name,name,xMin,xMax)
    obs = ROOT.RooArgList(disc)
    #

ROOT.gROOT.SetStyle("Plain")

#order and add all together
final_histos = {}

print '\n\t--> Ordering and Adding Histos\n'

#print 'workspace_datacard-all_samples:',[all_histos['%s'%job][0] for job in all_samples]

#jobnames = [job.name for job in all_samples]


if merge: final_histos = final_histos_merge
elif not split or (split and not split_data):
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
    print 'add sample sys'
    print '==============\n'
    for item in list(sample_sys_info.keys()):
        for Q in UD:
            final_histos['%s_%s'%(systematicsnaming[item],Q)]= HistoMaker.orderandadd([all_histos[job.name][ind] for job in all_samples],setup)
            ind+=1

    #print 'add lhe sys'
    #print '==============\n'
    #if len(lhe_muF)==2:
    #    for Q in UD:
    #        for group in sys_lhe_affecting.keys():
    #            histos = []
    #            for job in all_samples:
    #                if Dict[GroupDict[job.name]] in sys_lhe_affecting[group]:
    #                    print "XXX"
    #                    histos.append(all_histos[job.name][ind])
    #            final_histos['%s_%s_%s'%(systematicsnaming['lhe_muF'],group,Q)]= HistoMaker.orderandadd(histos,setup)
    #        ind+=1
    #
    #if len(lhe_muR)==2:
    #    for Q in UD:
    #        for group in sys_lhe_affecting.keys():
    #            histos = []
    #            for job in all_samples:
    #                if Dict[GroupDict[job.name]] in sys_lhe_affecting[group]:
    #                    print "XXX"
    #                    histos.append(all_histos[job.name][ind])
    #            final_histos['%s_%s_%s'%(systematicsnaming['lhe_muR'],group,Q)]= HistoMaker.orderandadd(histos,setup)
    #        ind+=1



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
                print "EEE"
                alternate = copy(all_histos[asample_dict[job.name]][0])
                hUp, hDown = get_alternate_shape(nominal[nominal.keys()[0]],alternate[alternate.keys()[0]])
                alternate_shapes_up.append({nominal.keys()[0]:hUp})
                alternate_shapes_down.append({nominal.keys()[0]:hDown})
            else:
                print "RRR"
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

if not split_data:
    if not ignore_stats:
        #make statistical shapes:
        print 'Make the statistical shapes'
        print '===========================\n'
        if not binstat:
            pass
        #    for Q in UD:
        #        final_histos['%s_%s'%(systematicsnaming['stats'],Q)] = {}
        #    for job,hist in final_histos['nominal'].items():
        #        errorsum=0
        #        for j in range(hist.GetNbinsX()+1):
        #            errorsum=errorsum+(hist.GetBinError(j))**2
        #        errorsum=sqrt(errorsum)
        #        total=hist.Integral()
        #        for Q in UD:
        #            final_histos['%s_%s'%(systematicsnaming['stats'],Q)][job] = hist.Clone()
        #            for j in range(hist.GetNbinsX()+1):
        #                if Q == 'Up':
        #                    if rescaleSqrtN and total:
        #                        final_histos['%s_%s'%(systematicsnaming['stats'],Q)][job].SetBinContent(j,max(1.E-6,hist.GetBinContent(j)+hist.GetBinError(j)/total*errorsum))
        #                    else:
        #                        final_histos['%s_%s'%(systematicsnaming['stats'],Q)][job].SetBinContent(j,max(1.E-6,hist.GetBinContent(j)+hist.GetBinError(j)))
        #                if Q == 'Down':
        #                    if rescaleSqrtN and total:
        #                        final_histos['%s_%s'%(systematicsnaming['stats'],Q)][job].SetBinContent(j,max(1.E-6,hist.GetBinContent(j)-hist.GetBinError(j)/total*errorsum))
        #                    else:
        #                        final_histos['%s_%s'%(systematicsnaming['stats'],Q)][job].SetBinContent(j,max(1.E-6,hist.GetBinContent(j)-hist.GetBinError(j)))
        else:
            print "Running Statistical uncertainty"
            threshold =  0.5 #stat error / sqrt(value). It was 0.5
            print "threshold",threshold
            binsBelowThreshold = {}
            for bin in range(1,nBins+1):
                if not merge:
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
                    if not merge:
                        for Q in UD:
                            final_histos['%s_bin%s_%s'%(systematicsnaming['stats'],bin,Q)][job] = hist.Clone()
                            if Q == 'Up':
                                final_histos['%s_bin%s_%s'%(systematicsnaming['stats'],bin,Q)][job].SetBinContent(bin,max(1.E-6,hist.GetBinContent(bin)+hist.GetBinError(bin)))
                            if Q == 'Down':
                                final_histos['%s_bin%s_%s'%(systematicsnaming['stats'],bin,Q)][job].SetBinContent(bin,max(1.E-6,hist.GetBinContent(bin)-hist.GetBinError(bin)))



#print "binsBelowThreshold:",binsBelowThreshold
print 'Start writing shapes in WS'
print '==========================\n'
print 'final_histos:',final_histos
#write shapes in WS:
for key in final_histos:
    for job, hist in final_histos[key].items():
        if 'nominal' == key:
            hist.SetName('%s'%(Dict[job]))
            hist.Write()
            #rooDataHist = ROOT.RooDataHist('%s' %(Dict[job]),'%s'%(Dict[job]),obs, hist)
            #getattr(WS,'import')(rooDataHist)
        for Q in UD:
            if Q in key:
                if key.endswith('_%s'%Q):
                    theSyst = ''.join(key.rsplit('_%s'%Q,1))
                elif key.endswith('%s'%Q):
                    theSyst = ''.join(key.rsplit('%s'%Q,1))
                #else:
                #    print '@ERROR: sys does not end by Up/Down. Aborting'
                #    print 'sys is',  key
                #    sys.exit()
            else:
                continue
            if systematicsnaming['stats'] in key:
                if merge:
                    nameSyst = theSyst
                else:
                    nameSyst = '%s_%s_%s' %(theSyst,Dict[job],Datacardbin)
            elif systematicsnaming['model'] in key:
                nameSyst = '%s_%s' %(theSyst,Dict[job])
            else:
                nameSyst = theSyst
            hist.SetName('%s%s%s' %(Dict[job],nameSyst,Q))
            hist.Write()
            #rooDataHist = ROOT.RooDataHist('%s%s%s' %(Dict[job],nameSyst,Q),'%s%s%s'%(Dict[job],nameSyst,Q),obs, hist)
            #getattr(WS,'import')(rooDataHist)


if not split or (split and split_data):
    if toy or signal_inject:
        hDummy.SetName('data_obs')
        hDummy.Write()
        rooDataHist = ROOT.RooDataHist('data_obs','data_obs',obs, hDummy)
    else:
        theData.SetName('data_obs')
        theData.Write()
        rooDataHist = ROOT.RooDataHist('data_obs','data_obs',obs, theData)

#getattr(WS,'import')(rooDataHist)

#WS.writeToFile(outpath+'vhbb_WS_'+ROOToutname+'.root')

# now we have a Dict final_histos with sets of all grouped MCs for all systematics:
# nominal, ($SYS_Up/Down)*4, weightF_sys_Up/Down, stats_Up/Down

if not split_data:
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
#for DCtype in ['WS','TH']:

DCtype = 'TH'

columns=len(setup)
#fileName = outpath+'vhbb_DC_%s_%s.txt'%(DCtype,ROOToutname)

if split:
    dc_dir = outpath+'vhbb_TH_'+ROOToutname
    #print 'the filname is', dc_dir+'/vhbb_DC_%s_%s_%i.txt'%(DCtype,ROOToutname,split_number)
    fileName = dc_dir+'/vhbb_dc_%s_%s_%i.txt'%(DCtype,ROOToutname,split_number)
    f = open(fileName,'w')
else:
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
    if not split or (split and split_data):
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
#count #of signal processes
SigProcess = []
for _sig in signals:
    if not GroupDict[_sig] in SigProcess: SigProcess.append(GroupDict[_sig])
    else: continue
nSig = len(SigProcess)
#print 'SigProcess is', SigProcess
#print 'nSig is', nSig

for c in range(1,columns+1): f.write('\t%s'%(c-nSig))
#for c in range(0,columns): f.write('\t%s'%(c-len(signals)+4))
#VH
#for c in range(0,columns): f.write('\t%s'%(c-len(signals)+3))
#VV
#for c in range(0,columns): f.write('\t%s'%(c-len(signals)))
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
            if '_eff_e' in item and 'Zuu' in ROOToutname : f.write('\t-')
            elif '_eff_m' in item and 'Zee' in ROOToutname : f.write('\t-')
            elif '_trigger_e' in item and 'Zuu' in ROOToutname : f.write('\t-')
            elif '_trigger_m' in item and 'Zee' in ROOToutname : f.write('\t-')
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
        pass
    #    for c in setup:
    #        f.write('%s_%s_%s\tshape'%(systematicsnaming['stats'],Dict[c],Datacardbin))
    #        for it in range(0,columns):
    #            if it == setup.index(c):
    #                f.write('\t1.0')
    #            else:
    #                f.write('\t-')
    #        f.write('\n')
# UEPS systematics
for weightF_sys in weightF_systematics:
    f.write('%s\tshape' %(systematicsnaming[weightF_sys]))
    for it in range(0,columns):
        for c in setup:
            if not it == setup.index(c): continue
            #if  setup[it] in exclude_sys_weight and weightF_sys in exclude_sys_weight[setup[it]]: f.write('\t-')
            #else: f.write('\t1.0')
            if  weightF_sys in decorrelate_sys_weight:
                if setup[it] in decorrelate_sys_weight[weightF_sys]: f.write('\t1.0')
                else: f.write('\t-')
            else: f.write('\t1.0')
            #if  setup[it] in decorrelate_sys_weight and weightF_sys in decorrelate_sys_weight[setup[it]]: f.write('\t1.0')
    f.write('\n')

# additional sample systematics
for key, item in sample_sys_info.iteritems():#loop over sys
    f.write('%s\tshape'%(systematicsnaming[key]))
    for it in range(0,columns):
        found = False
        for item2 in item:#loop over sample
            for c in setup:
                if not it == setup.index(c): continue
                for sample_type in item2:
                    if c in [GroupDict[d] for d in sample_type[0]]:
                        found = True
                        #print 'c is'
                        #print 'sample_type is', sample_type[0]
        if found: f.write('\t1.0')
        else: f.write('\t-')
    f.write('\n')

#OLD
#for weightF_sys in weightF_systematics:
#    print 'the sys is', systematicsnaming[weightF_sys]
#    f.write('%s\tshape' %(systematicsnaming[weightF_sys]))
#    for it in range(0,columns): f.write('\t1.0')
#    f.write('\n')
# LHE systematics
#if len(lhe_muF)==2:
#    for group in sys_lhe_affecting.keys():
#        f.write('%s_%s\tshape' %(systematicsnaming['lhe_muF'],group))
#        samples = sys_lhe_affecting[group]
#        for c in setup:
#            if Dict[c] in samples:
#                f.write('\t1.0')
#            else:
#                f.write('\t-')
#        f.write('\n')
#if len(lhe_muR)==2:
#    for group in sys_lhe_affecting.keys():
#        f.write('%s_%s\tshape' %(systematicsnaming['lhe_muR'],group))
#        samples = sys_lhe_affecting[group]
#        for c in setup:
#            if Dict[c] in samples:
#                f.write('\t1.0')
#            else:
#                f.write('\t-')
#        f.write('\n')
# additional sample systematics
#if addSample_sys:
#    alreadyAdded = []
#    for newSample in addSample_sys.iterkeys():
#        for c in setup:
#            if not c == GroupDict[newSample]: continue
#            if Dict[c] in alreadyAdded: continue
#            if final_histos['nominal'][c].Integral()<0.1: continue #skip model syst for negligible samples (eg. ggZH in W+Light CR)
#            f.write('%s_%s\tshape'%(systematicsnaming['model'],Dict[c]))
#            for it in range(0,columns):
#                if it == setup.index(c):
#                     f.write('\t1.0')
#                else:
#                     f.write('\t-')
#            f.write('\n')
#            alreadyAdded.append(Dict[c])
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
try:
    rateParamRange=eval(config.get('Datacard','rateParamRange'))
except:
    rateParamRange=[0,10]
assert len(rateParamRange) is 2, 'rateParamRange is not 2! rateParamRange:'+ len(rateParamRange)
for rateParam in rateParams:
    dictProcs=eval(config.get('Datacard',rateParam))
    for proc in dictProcs.keys():
        f.write(rateParam+'\trateParam\t'+Datacardbin+'\t'+proc+'\t'+str(dictProcs[proc])+' ['+str(rateParamRange[0])+','+str(rateParamRange[1])+']\n')
        #f.write(rateParam+'\trateParam\t'+Datacardbin+'\t'+proc+'\t'+str(dictProcs[proc])+'\n')

f.close()
useSpacesInDC(fileName)
print 'end useSpacesInDC'

# --------------------------------------------------------------------------

outfile.Write()
outfile.Close()
print 'closed outputfile'
