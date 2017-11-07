#! /usr/bin/env python
from optparse import OptionParser
import sys
import time,datetime
import os
import shutil
import subprocess
import hashlib
import signal
import zlib
import base64
from myutils.sampleTree import SampleTree as SampleTree
from myutils.FileList import FileList
from myutils.Datacard import Datacard

parser = OptionParser()
parser.add_option("-T", "--tag", dest="tag", default="8TeV",
                      help="Tag to run the analysis with, example '8TeV' uses config8TeV and pathConfig8TeV to run the analysis")
parser.add_option("-J", "--task", dest="task", default="",
                      help="Task to be done, i.e. 'dc' for Datacards, 'prep' for preparation of Trees, 'plot' to produce plots or 'eval' to write the MVA output or 'sys' to write regression and systematics (or 'syseval' for both). ")
parser.add_option("-M", "--mass", dest="mass", default="125",
              help="Mass for DC or Plots, 110...135")
parser.add_option("-S","--samples",dest="samples",default="",
              help="samples you want to run on")
parser.add_option("-F", "--folderTag", dest="ftag", default="",
                      help="Creats a new folder structure for outputs or uses an existing one with the given name")
parser.add_option("-N", "--number-of-events-or-files", dest="nevents_split_nfiles_single", default=-1,
                      help="Number of events per file when splitting or number of files when using single file workflow.")
parser.add_option("-P", "--philipp-love-progress-bars", dest="philipp_love_progress_bars", default=False,
                      help="If you share the love of Philipp...")
parser.add_option("-V", "--verbose", dest="verbose", action="store_true", default=False,
                      help="Activate verbose flag for debug printouts")
parser.add_option("-L", "--local", dest="override_to_run_locally", action="store_true", default=False,
                      help="Override run_locally option to run locally")
parser.add_option("-B", "--batch", dest="override_to_run_in_batch", action="store_true", default=False,
                      help="Override run_locally option to run in batch")
parser.add_option("-m", "--monitor", dest="monitor_only", action="store_true", default=False,
                      help="Override run_locally option to run in batch")
parser.add_option("-i", "--interactive", dest="interactive", action="store_true", default=False,
                              help="Interactive mode")
parser.add_option("-f", "--force", dest="force", action="store_true", default=False,
                      help="Force overwriting of files if they already exist")

(opts, args) = parser.parse_args(sys.argv)
#print 'opts.mass is', opts.mass

import os,shutil,pickle,subprocess,ROOT,re
ROOT.gROOT.SetBatch(True)
from myutils import BetterConfigParser, Sample, ParseInfo, sample_parser, copytreePSI
from myutils.copytreePSI import filelist
import getpass

debugPrintOUts = opts.verbose

if opts.tag == "":
    print "Please provide tag to run the analysis with, example '-T 8TeV' uses config8TeV and pathConfig8TeV to run the analysis."
    sys.exit(123)

if opts.task == "":
    print "Please provide a task.\n-J prep:\tpreparation of Trees\n-J sys:\t\twrite regression and systematics\n-J eval:\tcreate MVA output\n-J plot:\tproduce Plots\n-J dc:\t\twrite workspaces and datacards"
    sys.exit(123)

globalFilesSubmitted = 0
globalFilesSkipped = 0

def signal_handler(signal, frame):
    if (globalFilesSubmitted > 0 or globalFilesSkipped > 0):
        print('\n----------------------------\n')
        print('Files submitted:'+str(globalFilesSubmitted))
        print('Files skipped:'+str(globalFilesSkipped))
    print('You pressed Ctrl+C!')
    print('\n----------------------------\n')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

en = opts.tag

#create the list with the samples to run over
samplesList=opts.samples.split(",")
# timestamp = time.asctime().replace(' ','_').replace(':','-')
timestamp = time.strftime("%Y_%m_%d-%H_%M_%S")

if(debugPrintOUts): print 'samplesList',samplesList
if(debugPrintOUts): print 'timestamp',timestamp

# the list of the config is taken from the path config
pathconfig = BetterConfigParser()
pathconfig.read('%sconfig/paths.ini'%(en))
_configs = pathconfig.get('Configuration','List').split(" ")
configs = [ '%sconfig/'%(en) + c for c in _configs  ]

if(debugPrintOUts): print 'configs',configs
if(debugPrintOUts): print 'opts.ftag',opts.ftag

if not opts.ftag == '':
    tagDir = pathconfig.get('Directories','tagDir')
    if(debugPrintOUts): print 'tagDir',tagDir
    DirStruct={'tagDir':tagDir,'ftagdir':'%s/%s/'%(tagDir,opts.ftag),'logpath':'%s/%s/%s/'%(tagDir,opts.ftag,'Logs'),'plotpath':'%s/%s/%s/'%(tagDir,opts.ftag,'Plots'),'limitpath':'%s/%s/%s/'%(tagDir,opts.ftag,'Limits'),'confpath':'%s/%s/%s/'%(tagDir,opts.ftag,'config') }

    if(debugPrintOUts): print 'DirStruct',DirStruct

    for keys in ['tagDir','ftagdir','logpath','plotpath','limitpath','confpath']:
        try:
            os.stat(DirStruct[keys])
        except:
            os.mkdir(DirStruct[keys])

    pathfile = open('%sconfig/paths.ini'%(en))
    buffer = pathfile.readlines()
    pathfile.close()
    os.rename('%sconfig/paths.ini'%(en),'%sconfig/paths.ini.bkp'%(en))
    pathfile = open('%sconfig/paths.ini'%(en),'w')
    for line in buffer:
        if line.startswith('plotpath'):
            line = 'plotpath: %s\n'%DirStruct['plotpath']
        elif line.startswith('logpath'):
            line = 'logpath: %s\n'%DirStruct['logpath']
        elif line.startswith('limits'):
            line = 'limits: %s\n'%DirStruct['limitpath']
        pathfile.write(line)
    pathfile.close()

    #copy config files
    for item in configs:
        shutil.copyfile(item,'%s/%s/%s'%(tagDir,opts.ftag,item.replace(en, '')))

if(debugPrintOUts): print configs
config = BetterConfigParser()
config.read(configs)

# RETRIEVE RELEVANT VARIABLES FROM CONFIG FILES AND FROM COMMAND LINE OPTIONS
logPath = config.get("Directories","logpath")
logo = open('%s/data/submit.txt' %config.get('Directories','vhbbpath')).readlines()
counter = 0
samplesinfo = config.get("Directories","samplesinfo")
whereToLaunch = config.get('Configuration','whereToLaunch')
run_locally = str(config.get("Configuration","run_locally"))
if opts.override_to_run_locally and opts.override_to_run_in_batch:
    print 'both override_to_run_locally and override_to_run_in_batch ativated, using str(config.get("Configuration","run_locally")) instead'
elif opts.override_to_run_locally:
    run_locally = 'True'
    print 'using override_to_run_locally to override str(config.get("Configuration","run_locally"))'
elif opts.override_to_run_in_batch:
    run_locally = 'False'
    print 'using override_to_run_in_batch to override str(config.get("Configuration","run_locally"))'

print 'whereToLaunch',whereToLaunch
print 'run_locally',run_locally

# CREATE DIRECTORIES FOR PSI
if 'PSI' in whereToLaunch:
  print 'Create the ouput folders PREPout, SYSout, MVAout if not existing'
  mkdir_list = [
                config.get('Directories','PREPout').replace('root://t3dcachedb03.psi.ch:1094/',''),
                config.get('Directories','SYSout').replace('root://t3dcachedb03.psi.ch:1094/',''),
                config.get('Directories','MVAout').replace('root://t3dcachedb03.psi.ch:1094/',''),
                config.get('Directories','tmpSamples').replace('root://t3dcachedb03.psi.ch:1094/',''),
                ]
  for mkdir_protocol in mkdir_list:
    if(debugPrintOUts): print 'checking',mkdir_protocol
    _output_folder = ''
    for _folder in mkdir_protocol.split('/'):
        _output_folder += '/'+_folder
        if not os.path.exists(_output_folder):
            command = "uberftp t3se01 'mkdir " + _output_folder + " ' "
            if(debugPrintOUts): print 'command is',command
            subprocess.call([command], shell = True)

def dump_config(configs,output_file):
    """
    Dump all the configs in a output file
    Args:
        output_file: the file where the log will be dumped
        configs: list of files (string) to be dumped
    Returns:
        nothing
    """
    outf = open(output_file,'w')
    for i in configs:
        try:
            f=open(i,'r')
            outf.write(f.read())
        except: print '@WARNING: Config' + i + ' not found. It will not be used.'

# TODO: binary files compiled by this function do not work (30.10.2017) 
def compile_macro(config,macro):
    """
    Creates the library from a macro using CINT compiling it in scratch to avoid
    problems with the linking in the working nodes.
    Args:
        config: configuration file where the macro path is specified
        macro: macro name to be compiled
    Returns:
        nothing
    """
    submitDir = os.getcwd()
    _macro=macro+'.h'
    library = config.get(macro,'library')
    libDir=os.path.dirname(library)
    os.chdir(libDir)
    if not os.path.exists(library):
        print '@INFO: Compiling ' + _macro
        scratchDir='/scratch/%s/'%(getpass.getuser())
        # shutil.copyfile(libDir+'/'+_macro,'/scratch/%s/%s'%(getpass.getuser(),_macro))
        os.system("cp "+libDir+'/* /scratch/%s/'%(getpass.getuser())) # OTHERWISE WILL NOT COMPILE SINCE INCLUDES OTHER FILES!!!
        os.chdir(scratchDir)
        print os.listdir(scratchDir)
        ROOT.gROOT.ProcessLine('.L %s+'%(scratchDir+_macro)) # CRASHES WHILE COMPILING THE SECOND ONE...
        shutil.copyfile('/scratch/%s/%s'%(getpass.getuser(),os.path.basename(library)),library)
        print '@INFO: macro',macro,'compiled, exiting to avoid stupid ROOT crash, please resubmit!!!'
        sys.exit(1)
    os.chdir(submitDir)

def training(additional_):

    train_list = [x.strip() for x in (config.get('MVALists','List_for_submitscript')).split(',')]
    print train_list
    for item in train_list:
        #No subcut declared. Just perform classical training
        if not config.has_option(item, 'subcut'):
            repDict['additional']= additional_ 
            print 'No subcuts in this training'
            submit(item,repDict)
            continue
        #subcut_ = eval(config.get(item,'subcut'))
        subcut = eval(config.get(item,'subcut'))
        print 'subcut_ is', subcut
        #Performs loop over all the subcuts to create corresponding bins
        for cutvar, CUTBIN in subcut.iteritems():
            print 'cutvar is', cutvar
            #cutbin_first = CUTBIN[0]
            for cutbins in CUTBIN:
                print 'cutbins is', cutbins
                cut_ = 'CUTBIN_%s__%g__%g'%(cutvar,cutbins[0], cutbins[1])
                print 'cut_ is', cut_
                #Need to propagate the cutbin param
                repDict['additional']= additional_ +'__'+cut_
                submit(item,repDict, False)

def ploting(additional_ = None, splitvar = False, splitfiles = False):
    repDict['additional'] = 'dummy'
    repDict['queue'] = 'all.q'
    for region in Plot_vars:
        section='Plot:%s'%region
        if not config.has_option(section, 'subcut'):
            print 'No subcut for the plot region', region
            if splitvar:
                vars = [x.strip() for x in (config.get('Plot:%s'%region, 'vars')).split(',')]
                for var in vars:
                    var_ = 'VAR_%s'%(var)
                    if additional_: repDict['additional']= additional_ +'__'+var_
                    else: repDict['additional']= var_
                    print 'additional is', repDict['additional']
                    #sys.exit()
                    submit(region,repDict)
            else: submit(region,repDict)
        else:
            subcut = eval(config.get(section,'subcut'))
            print 'splitvar is', splitvar
            print 'subcut is', subcut
            for cutvar, CUTBIN in subcut.iteritems():
                print 'cutvar is', cutvar
                #cutbin_first = CUTBIN[0]
                for cutbins in CUTBIN:
                    print 'cutbins is', cutbins
                    cut_ = 'CUTBIN_%s__%g__%g'%(cutvar,cutbins[0], cutbins[1])
                    print 'cut_ is', cut_
                    #Need to propagate the cutbin param
                    if additional_: repDict['additional']= additional_ +'__'+cut_
                    else: repDict['additional']= cut_
                    submit(region,repDict)


print '===============================\n'
print 'Compiling the macros'
print '===============================\n'
# compile_macro(config,'BTagReshaping')
compile_macro(config,'VHbbNameSpace')

#check if the logPath exist. If not exit
if( not os.path.isdir(logPath) ):
    print '@ERROR : ' + logPath + ': dir not found.'
    print '@ERROR : Create it before submitting '
    print 'Exit'
    sys.exit(-1)

# CREATE DICTIONARY TO BE USED AT JOB SUBMISSION TIME
repDict = {'en':en,'logpath':logPath,'job':'','task':opts.task,'queue': 'all.q','timestamp':timestamp,'additional':'','job_id':'noid','nprocesses':str(max(int(pathconfig.get('Configuration','nprocesses')),1))}

list_submitted_singlejobs = {}

# STANDARD WORKFLOW SUBMISSION FUNCTION
def submit(job,repDict,redirect_to_null=False):
    global counter
    repDict['job'] = job
    nJob = counter % len(logo)
    counter += 1
    if opts.philipp_love_progress_bars:
        repDict['name'] = '"%s"' %logo[nJob].strip()
    else:
        repDict['name'] = '%(job)s_%(en)s%(task)s' %repDict

    # run script
    runScript = 'runAll.sh %(job)s %(en)s '%(repDict)
    runScript += opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + repDict['additional']

    # add named arguments to run script
    if 'arguments' in repDict:
        for argument, value in repDict['arguments'].iteritems():
            runScript += (' --{argument}={value} '.format(argument=argument, value=value)) if len('{value}'.format(value=value)) > 0 else ' --{argument} '.format(argument=argument)

    # submit script
    if run_locally == 'False':
        logOutputPath = '%(logpath)s/%(task)s_%(timestamp)s_%(job)s_%(en)s_%(additional)s.out' %(repDict)
        qsubOptions = '-V -cwd -q %(queue)s -N %(name)s -j y -pe smp %(nprocesses)s' %(repDict) 

        if opts.task in ['mergesyscachingdcsplit', 'singleeval', 'cacheplot', 'cachetraining']:
            qsubOptions += ' -l h_vmem=6g '

        command = 'qsub {options} -o {logfile} {runscript}'.format(options=qsubOptions, logfile=logOutputPath, runscript=runScript)
        dump_config(configs,"%(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.config" %(repDict))
    else:
        waiting_time_before_retry = 60
        number_symultaneous_process = 2
        counter  =  int(subprocess.check_output('ps aux | grep $USER | grep \'sh runAll.sh\' | grep '+opts.task +' | wc -l', shell=True))-1# add 1 to remove submithem count
        print 'counter command is', 'ps aux | grep $USER | grep \'sh runAll.sh\' | grep '+opts.task +' | wc -l'
        while counter > number_symultaneous_process:
            print 'counter is', counter
            print 'waiting',waiting_time_before_retry,'seconds before to retry'
            os.system('sleep '+str(waiting_time_before_retry))
            counter = int(subprocess.check_output('ps aux | grep $USER | grep \'sh runAll.sh\' | grep '+opts.task +' | wc -l', shell=True))

        command = 'sh {runscript}'.format(runscript=runScript)

        if redirect_to_null: command = command + ' 2>&1 > /dev/null &'
        else: command = command + ' 2>&1 > %(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s_%(additional)s.out' %(repDict) + ' &'
        dump_config(configs,"%(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.config" %(repDict))

    # run command
    if opts.interactive:
        print "the real command is:\x1b[34m",command,"\x1b[0m\n(press ENTER to run it and continue)"
        answer = raw_input().strip()
        if answer == 'no' or answer == 'skip':
            return
    else:
        print "the command is ", command

    subprocess.call([command], shell=True)

# SINGLE (i.e. FILE BY FILE) AND SPLITTED FILE WORKFLOW SUBMISSION FUNCTION
def checksinglestep(repDict,run_locally,counter_local,Plot,file="none",sample="nosample"):
    global counter
    nJob = counter % len(logo)
    counter += 1
    task = opts.task
    if file != "none":
        task = "check"+opts.task
    command = 'sh runAll.sh '+str(sample)+' %(en)s ' %(repDict) + task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
    print "the command is ", command
    command = command + ' "' + str(file)+ '"' + ' "' + str(Plot)+ '"'
    return subprocess.call([command], shell=True)

# SINGLE (i.e. FILE BY FILE) AND SPLITTED FILE WORKFLOW SUBMISSION FUNCTION
def submitsinglefile(job,repDict,file,run_locally,counter_local,Plot,resubmit=False):
    global counter
    repDict['job'] = job
    repDict['joblogname'] = job.replace(',','_')
    nJob = counter % len(logo)
    counter += 1
    if opts.philipp_love_progress_bars:
        repDict['name'] = '"%s"' %logo[nJob].strip()
    else:
        repDict['name'] = '%(job)s_%(en)s%(task)s' %repDict
        repDict['name'] = repDict['name'].replace(',','_')+'_'+str(counter_local)
    repDict['logname'] =  ('%(task)s_%(timestamp)s_%(job)s_%(en)s_%(additional)s.out' %(repDict)).replace(',','_')
    if run_locally == 'True':
        command = 'sh runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
    else:
        if opts.task == 'mergesyscachingdcsplit' or opts.task == 'singleeval':
            command = 'qsub -l h_vmem=6g -V -cwd -q %(queue)s -N %(name)s -j y -o %(logpath)s/%(task)s_%(timestamp)s_%(joblogname)s_%(en)s_%(additional)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
        else:
            command = 'qsub -V -cwd -q %(queue)s -N %(name)s -j y -o %(logpath)s/%(task)s_%(timestamp)s_%(joblogname)s_%(en)s_%(additional)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
        command = command.replace('.out','_'+str(counter_local)+'.out')
    list_submitted_singlejobs[repDict['name']] = [file,1]
    #print "the command is ", command
    nFiles = len(file.split(';'))
    #print "submitting", nFiles, 'files like',file.split(';')[0]
    filelistString = str(file)
    command = command + ' "' + filelistString + '"' + ' "' + str(Plot)+ '"'
    if opts.interactive:
        print "the real command is:",command
        print "(press ENTER to run it and continue)"
        answer = raw_input().strip()
        if answer == 'no' or answer == 'skip':
            return
    dump_config(configs,"%(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.config" %(repDict))
    if (not opts.monitor_only) or resubmit:
        subprocess.call([command], shell=True)
# MERGING FUNCTION FOR SINGLE (i.e. FILE BY FILE) AND SPLITTED FILE WORKFLOW TO BE COMPATIBLE WITH THE OLD WORKFLOW
def mergesubmitsinglefile(job,repDict,run_locally,Plot):
    global counter
    repDict['job'] = job
    nJob = counter % len(logo)
    counter += 1
    if opts.philipp_love_progress_bars:
        repDict['name'] = '"%s"' %logo[nJob].strip()
    else:
        repDict['name'] = ('%(job)s_%(en)s%(task)s' %repDict).replace(',','_')
    repDict['logname'] =  ('%(task)s_%(timestamp)s_%(job)s_%(en)s_%(additional)s.out' %(repDict)).replace(',','_')
    if run_locally == 'True':
        command = 'sh runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
    else:
        if opts.task == 'mergesyscachingdcsplit' or opts.task == 'singleeval':
            command = 'qsub -l h_vmem=6g -V -cwd -q %(queue)s -N %(name)s -j y -o %(logpath)s/%(task)s_%(timestamp)s_%(job)s_%(en)s_%(additional)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
        else:
            command = 'qsub -V -cwd -q %(queue)s -N %(name)s -j y -o %(logpath)s/%(task)s_%(timestamp)s_%(job)s_%(en)s_%(additional)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
    list_submitted_singlejobs[repDict['name']] = [file,1]
    command = command + ' mergeall' + ' "' + str(Plot)+ '"'
    print "the command is ", command
    dump_config(configs,"%(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.config" %(repDict))
    subprocess.call([command], shell=True)

def tmp_file_exists(hash, part):
    tmpDir = config.get('Directories','tmpSamples').replace('root://t3dcachedb03.psi.ch:1094/','')
    tmpFileName = '/tmp_%s_%d.root'%(hash, part)
    print 'filename %s' %(tmpFileName)
    return os.path.isfile(tmpDir + tmpFileName)
def subcut_tmpfile_exists(hash,part,cut):
    """Given the hash of the cached file and the subcut, check if the corresponding subcached file exists"""
    tmpDir = config.get('Directories','tmpSamples').replace('root://t3dcachedb03.psi.ch:1094/','')
    subcut_hash = hashlib.sha224('%s_%s'%('%s_%d'%(hash,part),cut)).hexdigest()
    tmpFileName = '/tmp_%s_%d.root'%(subcut_hash, part)
    print 'Cut %s, filename %s' %(cut,tmpFileName)
    print ('Command is os.path.isfile(%s)'%(tmpDir + tmpFileName))
    return os.path.isfile(tmpDir + tmpFileName)

#To retrieve dc hash
from copy import copy, deepcopy
def return_splitcaching_hash(treecut,isdata):

    optionsList=[]
    shapecutList=[]
    _cut = 'dummy'
    _treevar = 'dummy'
    _name = 'dummy'
    nBins = 'dummy'
    xMin = 'dummy'
    xMax = 'dummy'
    _weight = 'dummy'
    _countHisto = 'dummy'
    _countbin = 'dummy'
    blind = 'dummy'
    shapecut = 'dummy'
    def appendSCList(): shapecutList.append(shapecut)
    def appendList(): optionsList.append({'cut':copy(_cut),'var':copy(_treevar),'name':copy(_name),'nBins':nBins,'xMin':xMin,'xMax':xMax,'weight':copy(_weight),'countHisto':copy(_countHisto),'countbin':copy(_countbin),'blind':blind})

    optionsList=[]
    shapecutList=[]
    systematics = eval(config.get('LimitGeneral','sys_BDT'))
    sys_cut_suffix=eval(config.get('LimitGeneral','sys_cut_suffix'))
    sys_weight_corr=eval(config.get('LimitGeneral','sys_weight_corr'))
    weightF_systematics = eval(config.get('LimitGeneral','weightF_sys'))

    lhe_muF = []
    lhe_muR = []
    if config.has_option('LimitGeneral','sys_lhe_muF_BDT'): lhe_muF = eval(config.get('LimitGeneral','sys_lhe_muF_BDT'))
    if config.has_option('LimitGeneral','sys_lhe_muR_BDT'): lhe_muR = eval(config.get('LimitGeneral','sys_lhe_muR_BDT'))

    #initalize everything to go trough the code snippet

    UD = ['Up','Down']
    #Here just copying from workspace dc
    title = ['dummy']

    _cut = treecut
    _treevar = 'dummy'
    treevar = 'dummy'
    _name = 'dummy'
    _weight = 'dummy'
    _countHisto = "dummy"
    weightF = 'dummy'
    bdt = True
    mjj = False
    _countbin = 0
    #shapecut = _cut
    #ie. take count from 'CountWeighted->GetBinContent(1)'
    appendList()
    #appendSCList()


    #all the cuts except the one modified by the shape variation
    shapecut= ''
    cutlist =  _cut.split('&')
    rmv_sys = _cut.split('&')
    sysnomcut = ''
    #print 'cutlist is ', cutlist

    #shape systematics
    for syst in systematics:
        for Q in UD:
            #print 'Q is', Q
            _cut = treecut
            _name = title
            _weight = weightF
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
                    #SYS = syst.split('_UD_')[0]
                    #CAT = syst.split('_UD_')[1]
                    #_cut = _cut.replace(old_str,new_str.replace('SYS',SYS).replace('CAT',CAT).replace('UD',Q))
                    #print 'new_str is', new_str
                    #print 'old_str is', old_str
                    _cut = _cut.replace(old_str,new_str.replace('SYS',syst).replace('UD',Q))
                    for c_ in cutlist:
                        if (old_str in c_) and (c_ in rmv_sys): rmv_sys.remove(c_)
                _name = title
                _weight = weightF
            #print ''

            if syst in sys_weight_corr:
                #print 'sys_weight is',sys_weight_corr[syst]+'_%s' %(Q.upper())
                _weight = config.get('Weights',sys_weight_corr[syst]+'_%s' %(Q.upper()))
                #print '_weight is', _weight
            #replace tree variable
            if bdt == True:
                #ff[1]='%s_%s'%(sys,Q.lower())
                #print 'old treevar', _treevar
                if not 'UD' in syst:
                    _treevar = treevar.replace('.nominal','.%s_%s'%(syst,Q.lower()))
                    #_treevar = treevar.replace('.Nominal','.%s_%s'%(syst,Q.lower()))
                else:
                    _treevar = treevar.replace('.nominal','.%s'%(syst.replace('UD',Q)))
                    #_treevar = treevar.replace('.Nominal','.%s'%(syst.replace('UD',Q)))
                    #print '.nominal by','.%s'%(syst.replace('UD',Q))
                #print 'treevar after replacement', _treevar
            elif mjj == True:
                if syst == 'JER':
                    _treevar = treevar.replace('_reg_mass','_reg_corrJER%s_mass'%Q)
                elif syst == 'JES':
                    _treevar = treevar.replace('_reg_mass','_reg_corrJEC%s_mass'%Q)
                else:
                    _treevar = treevar
            elif cr == True:
                _treevar = treevar
            #append
            appendList()
            #appendSCList()
            #print 'new tree cut is', _cut
    #print 'OPTIONSLIST IS',optionsList
    #print 'rmv_sys is', rmv_sys
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
                    #print 'when removing everything, string is', shape_.replace('>','').replace('<','').replace(' ','').replace('(','').replace(')','').replace('||','').replace(old_str,'')
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
                        #print 'newcut_ is ', newcut_
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

    shapecut_MinMax = '&'.join(shapecut_split)
    #print 'shapecut_MinMax is', shapecut_MinMax

    dccut = sysnomcut + '&(' + shapecut_MinMax + ')'
    dccutdata = sysnomcut + '&(' + shapecut_first + ')'
    #print 'dccut is', dccut
    #print 'dccutdata is', dccutdata

    #print 'after removing shape sys'
    #print 'shapecut', shapecut #this is the sys variable only
    #print 'shapecut_first', shapecut_first
    #print 'sysnomcut', sysnomcut #this is the cut string without the sys variables
    #appendSCList()
    #sys.exit(0)

    #dccut = sysnomcut

    #UEPS
    #Appends options for each weight
    for weightF_sys in weightF_systematics:
        #if '_eff_e' in weightF_sys and 'Zuu' in ROOToutname : continue
        #if '_eff_m' in weightF_sys and 'Zee' in ROOToutname : continue
        for _weight in [config.get('Weights','%s_UP' %(weightF_sys)),config.get('Weights','%s_DOWN' %(weightF_sys))]:
            #_cut = treecut
            #shapecut = sysnomcut
            _cut = "1"
            shapecut = "1"
            _treevar = treevar
            _name = title
            appendList()
            appendSCList()

    #lhe_muF
    #Appends options for each weight (up/down -> len =2 )
    if len(lhe_muF)==2:
        for lhe_muF_num in lhe_muF:
            _weight = weightF + "*LHE_weights_scale_wgt[%s]"%lhe_muF_num
            #_cut = treecut
            #shapecut = sysnomcut
            _cut = "1"
            shapecut = "1"
            _treevar = treevar
            _name = title
            _countHisto = "CountWeightedLHEWeightScale"
            _countbin = lhe_muF_num
            appendList()
            appendSCList()

    if len(lhe_muR)==2:
        for lhe_muR_num in lhe_muR:
            _weight = weightF + "*LHE_weights_scale_wgt[%s]"%lhe_muR_num
            #_cut = treecut
            #shapecut = sysnomcut
            _cut = "1"
            shapecut = "1"
            _treevar = treevar
            _name = title
            _countHisto = "CountWeightedLHEWeightScale"
            _countbin = lhe_muR_num
            appendList()
            appendSCList()

    if len(optionsList) != len(shapecutList):
        print '@ERROR: optionsList and shapecutList don\'t have equal size. Aborting'
        sys.exit()

    _countHisto = "CountWeighted"
    _countbin = 0

    #print '===================\n'
    #print 'comparing cut strings'
    for optold, optnew in zip(optionsList,shapecutList):
        #print 'old option is', optold['cut']
        #print 'new option is', optnew
        optionsList[optionsList.index(optold)]['cut']=optnew

    #making the final cut
    cutList = []
    for options in optionsList:
        cutList.append('(%s)'%options['cut'].replace(' ',''))


    #def __find_min_cut(cutList_):
    #    effective_cuts = []
    #    for cut in cutList_:
    #        if not cut in effective_cuts and not cut == "(1)":
    #            effective_cuts.append(cut)
    #    cutList_ = effective_cuts
    #    minCut = '||'.join(cutList_)
    #    #for dc step
    #    if dccut:
    #        minCut = '('+dccut+')&&('+minCut+')'

    #    return minCut

    #if isdata:
    #    cutList = [cutList[0]]

    #minCut = __find_min_cut(cutList)


    #print 'minCut is', minCut
    if isdata:
        return '('+dccutdata+')'
    else:
        return '('+dccut+')'
    return minCut


# RETRIEVE FILELIST FOR THE TREECOPIER PSI AND SINGLE FILE SYS STEPS
def getfilelist(job):
    samplefiles = config.get('Directories','samplefiles')
    list = filelist(samplefiles,job)
    return list


if opts.task == 'train':
    training('')
if opts.task == 'mergesubcachingtrain':
    training('')

elif opts.task == 'splitsubcaching':
    train_list = [x.strip() for x in (config.get('MVALists','List_for_submitscript')).split(',')]
    for region in train_list:
         print 'region is', region
         path = config.get("Directories","samplepath")
         samplesinfo=config.get('Directories','samplesinfo')
         info = ParseInfo(samplesinfo,path)
         signals = eval(config.get(region,'signals'))
         backgrounds = eval(config.get(region,'backgrounds'))
         samples = info.get_samples(signals+backgrounds)
         for sample in samples:
             print 'sample is', sample
             #repDict['additional']='CACHING'+'__'+str(sample)
             additional_ = 'CACHING'+'__'+str(sample)
             repDict['queue'] = 'all.q'
             training(additional_)

if opts.task.startswith('cachetraining'):
    trainingRegions = [x.strip() for x in (config.get('MVALists','List_for_submitscript')).split(',')]
    allBackgrounds = list(set(sum([eval(config.get(trainingRegion, 'backgrounds')) for trainingRegion in trainingRegions], [])))
    allSignals = list(set(sum([eval(config.get(trainingRegion, 'signals')) for trainingRegion in trainingRegions], [])))
    print "backgrounds:"
    for sampleName in sorted(allBackgrounds):
        print " >", sampleName
    print "signals:"
    for sampleName in sorted(allSignals):
        print " >", sampleName
    
    # get samples info
    info = ParseInfo(samplesinfo, config.get('Directories', 'MVAin'))
    samples = info.get_samples(allBackgrounds + allSignals)

    # find all sample identifiers that have to be cached, if given list is empty, run it on all
    samplesToCache = [x.strip() for x in opts.samples.strip().split(',') if len(x.strip()) > 0]
    sampleIdentifiers = sorted(list(set([sample.identifier for sample in samples if sample.identifier in samplesToCache or len(samplesToCache) < 1])))
    print "sample identifiers: (", len(sampleIdentifiers), ")"
    for sampleIdentifier in sampleIdentifiers:
        print " >", sampleIdentifier
    
    # submit separate jobs for all samples
    for sampleIdentifier in sampleIdentifiers:

        # number of files to process per job 
        splitFilesChunkSize = min([sample.mergeCachingSize for sample in samples if sample.identifier==sampleIdentifier])
        splitFilesChunks = SampleTree({'name': sampleIdentifier, 'folder': config.get('Directories', 'MVAin')}, countOnly=True, splitFilesChunkSize=splitFilesChunkSize, config=config).getSampleFileNameChunks()
        print "DEBUG: split after ", splitFilesChunkSize, " files => number of parts = ", len(splitFilesChunks)
        
        # submit all the single chunks for one sample
        for chunkNumber, splitFilesChunk in enumerate(splitFilesChunks, start=1):
            jobDict = repDict.copy()
            jobDict.update({
                'queue': 'short.q',
                'arguments':
                    {
                        'trainingRegions': ','.join(trainingRegions),
                        'sampleIdentifier': sampleIdentifier,
                        'chunkNumber': chunkNumber,
                        'splitFilesChunks': len(splitFilesChunks),
                        'splitFilesChunkSize': splitFilesChunkSize,
                    }
                })
            if opts.force:
                jobDict['arguments']['force'] = ''
            # pass file list, if only a chunk of it is processed
            if len(splitFilesChunks) > 1:
                compressedFileList = FileList.compress(splitFilesChunk)
                jobDict['arguments']['fileList'] = compressedFileList
            jobName = 'training_cache_{sample}_part{part}'.format(sample=sampleIdentifier, part=chunkNumber)
            submit(jobName, jobDict)

if opts.task.startswith('runtraining'):
    # training regions
    trainingRegions = [x.strip() for x in (config.get('MVALists', 'List_for_submitscript')).split(',')]

    # separate job for all training regions
    for trainingRegion in trainingRegions:
        jobDict = repDict.copy()
        jobDict.update({'arguments': {'trainingRegions': trainingRegion}})
        jobName = 'training_run_{trainingRegions}'.format(trainingRegions=trainingRegion)
        submit(jobName, jobDict)

if opts.task.startswith('cacheplot'):
    regions = [x.strip() for x in (config.get('Plot_general', 'List')).split(',')]
    sampleNames = eval(config.get('Plot_general', 'samples')) 
    dataSampleNames = eval(config.get('Plot_general', 'Data')) 

    # get samples info
    info = ParseInfo(samplesinfo, config.get('Directories', 'plottingSamples'))
    samples = info.get_samples(sampleNames + dataSampleNames)

    # find all sample identifiers that have to be cached, if given list is empty, run it on all
    samplesToCache = [x.strip() for x in opts.samples.strip().split(',') if len(x.strip()) > 0]
    sampleIdentifiers = sorted(list(set([sample.identifier for sample in samples if sample.identifier in samplesToCache or len(samplesToCache) < 1])))
    print "sample identifiers: (", len(sampleIdentifiers), ")"
    for sampleIdentifier in sampleIdentifiers:
        print " >", sampleIdentifier
    
    # submit jobs, 1 to n separate jobs per sample
    for sampleIdentifier in sampleIdentifiers:

        # number of files to process per job 
        splitFilesChunkSize = min([sample.mergeCachingSize for sample in samples if sample.identifier == sampleIdentifier])
        splitFilesChunks = SampleTree({'name': sampleIdentifier, 'folder': config.get('Directories', 'plottingSamples')}, countOnly=True, splitFilesChunkSize=splitFilesChunkSize, config=config).getSampleFileNameChunks()
        print "DEBUG: split after ", splitFilesChunkSize, " files => number of parts = ", len(splitFilesChunks)
        
        # submit all the single parts
        for chunkNumber, splitFilesChunk in enumerate(splitFilesChunks, start=1):
            compressedFileList = FileList.compress(splitFilesChunk)
            jobDict = repDict.copy()
            jobDict.update({
                    'queue': 'short.q',
                    'arguments':
                        {
                        'regions': ','.join(regions),
                        'sampleIdentifier': sampleIdentifier,
                        'chunkNumber': chunkNumber,
                        'splitFilesChunks': len(splitFilesChunks),
                        'splitFilesChunkSize': splitFilesChunkSize,
                        }
                    })
            if opts.force:
                jobDict['arguments']['force'] = ''
            # pass file list, if only a chunk of it is processed
            if len(splitFilesChunks) > 1:
                jobDict['arguments']['fileList'] = compressedFileList
            jobName = 'plot_cache_{sample}_part{chunk}'.format(sample=sampleIdentifier, chunk=chunkNumber)
            submit(jobName, jobDict)

if opts.task.startswith('runplot'):
    regions = [x.strip() for x in (config.get('Plot_general', 'List')).split(',')]

    # submit all the plot regions as separate jobs
    for region in regions:
        jobDict = repDict.copy()
        jobDict.update({
            'arguments':
                {
                    'regions': region,
                }
            })
        jobName = 'plot_run_{region}'.format(region=region)
        submit(jobName, jobDict)

if opts.task.startswith('cachedc'):
    # get list of all sample names used in DC step
    sampleNames = []
    regions = [x.strip() for x in config.get('LimitGeneral', 'List').split(',') if len(x.strip()) > 0]
    if config.has_option('LimitGeneral', 'addSample_sys'):
        addSample_sys = eval(config.get('LimitGeneral', 'addSample_sys'))
        sampleNames += [addSample_sys[key] for key in addSample_sys]
    for region in regions:
        for sampleType in ['data', 'signal', 'background']:
            sampleNames += eval(config.get('dc:%s'%region, sampleType))

    # get samples info
    sampleFolder = config.get('Directories', 'dcSamples')
    info = ParseInfo(samplesinfo, sampleFolder)
    samples = info.get_samples(sampleNames)

    # find all sample identifiers that have to be cached, if given list is empty, run it on all
    samplesToCache = [x.strip() for x in opts.samples.strip().split(',') if len(x.strip()) > 0]
    sampleIdentifiers = sorted(list(set([sample.identifier for sample in samples if sample.identifier in samplesToCache or len(samplesToCache) < 1])))
    print "sample identifiers: (", len(sampleIdentifiers), ")"
    for sampleIdentifier in sampleIdentifiers:
        print " >", sampleIdentifier
    
    # submit jobs, 1 to n separate jobs per sample
    for sampleIdentifier in sampleIdentifiers:

        # number of files to process per job 
        splitFilesChunkSize = min([sample.mergeCachingSize for sample in samples if sample.identifier == sampleIdentifier])
        splitFilesChunks = SampleTree({'name': sampleIdentifier, 'folder': sampleFolder}, countOnly=True, splitFilesChunkSize=splitFilesChunkSize).getSampleFileNameChunks()
        print "DEBUG: split after ", splitFilesChunkSize, " files => number of parts = ", len(splitFilesChunks)
        
        # submit all the single parts
        for chunkNumber, splitFilesChunk in enumerate(splitFilesChunks, start=1):
            compressedFileList = FileList.compress(splitFilesChunk)
            jobDict = repDict.copy()
            jobDict.update({
                'arguments':
                    {
                        'sampleIdentifier': sampleIdentifier,
                        'chunkNumber': chunkNumber,
                        'splitFilesChunks': len(splitFilesChunks),
                        'splitFilesChunkSize': splitFilesChunkSize,
                    }
                })
            # pass file list, if only a chunk of it is processed
            if len(splitFilesChunks) > 1:
                jobDict['arguments']['fileList'] = compressedFileList
            jobName = 'dc_cache_{sample}_part{chunk}'.format(sample=sampleIdentifier, chunk=chunkNumber)
            submit(jobName, jobDict)

if opts.task.startswith('rundc'):
    
    regions = Datacard.getRegions(config=config)
    samples = Datacard.getSamples(config=config, regions=regions)

    sampleIdentifiers = sorted(list(set([sample.identifier for sample in samples])))

    # only process given samples (if option is present)
    samplesToCache = [x.strip() for x in opts.samples.strip().split(',') if len(x.strip()) > 0]
    if len(samplesToCache) > 0:
        sampleIdentifiers = [x for x in sampleIdentifiers if x in samplesToCache]

    #DEBUG: sampleIdentifiers = [x for x in sampleIdentifiers if 'Double' in x]

    # submit all the DC regions as separate jobs
    for region in regions:
        # submit separate jobs for either sampleIdentifiers
        for sampleIdentifier in sampleIdentifiers: 
            jobDict = repDict.copy()
            jobDict.update({
                'queue': 'short.q',
                'arguments':
                    {
                        'regions': region,
                        'sampleIdentifier': sampleIdentifier,
                    }
                })
            jobName = 'dc_run_' + '_'.join([v for k,v in jobDict['arguments'].iteritems()])
            submit(jobName, jobDict)

if opts.task.startswith('mergedc'):
    regions = Datacard.getRegions(config=config)

    # submit all the DC regions as separate jobs
    for region in regions:
        jobDict = repDict.copy()
        jobDict.update({
            'queue': 'short.q',
            'arguments':
                {
                    'regions': region,
                }
            })
        jobName = 'dc_merge_' + '_'.join([v for k,v in jobDict['arguments'].iteritems()])
        submit(jobName, jobDict)

if opts.task == 'dc' or opts.task == 'mergesyscachingdc' or opts.task == 'mergesyscachingdcsplit' or opts.task == 'mergesyscachingdcmerge':
    DC_vars= [x.strip() for x in (config.get('LimitGeneral','List')).split(',')]
    print DC_vars

Plot_vars = ['']
if opts.task in ['plot', 'splitvarplot', 'singleplot', 'mergesingleplot', 'mergecachingplot','mergecachingplotvar']:
    Plot_vars= [x.strip() for x in (config.get('Plot_general','List')).split(',')]

if not opts.task == 'prep':
    path = config.get("Directories","samplepath")
    info = ParseInfo(samplesinfo,path)

if opts.task in ['plot', 'mergecachingplot']:
    ploting()

if opts.task == 'splitvarplot' or opts.task == 'mergecachingplotvar':
    ploting(None, True)

#Old and working
#if opts.task == 'plot':
#
#    repDict['queue'] = 'all.q'
#    for region in Plot_vars:
#        section='Plot:%s'%region
#        if not config.has_option(section, 'subcut'):
#            print 'No subcut for the plot region', region
#            submit(region,repDict)
#            continue
#        subcut = eval(config.get(section,'subcut'))
#        print 'subcut is', subcut
#        for cutvar, CUTBIN in subcut.iteritems():
#            print 'cutvar is', cutvar
#            #cutbin_first = CUTBIN[0]
#            for cutbins in CUTBIN:
#                print 'cutbins is', cutbins
#                cut_ = 'CUTBIN_%s__%g__%g'%(cutvar,cutbins[0], cutbins[1])
#                print 'cut_ is', cut_
#                #Need to propagate the cutbin param
#                repDict['additional']= cut_
#                submit(region,repDict)

#if opts.task == 'splitcaching':
#    plitcaching()

if opts.task == 'mergecaching2':

    samplesinfo = config.get('Directories', 'samplesinfo')
    info = ParseInfo(samplesinfo,path)
    print info

    # get all regions
    regions = [x.strip() for x in config.get('Plot_general', 'List').split(',')]

    # determine which regions are compatible to be cached together in one go
    regionsDict = {}
    for region in regions:
        section = 'Plot:%s'%region
        dataSamples = eval(config.get(section, 'Datas'))
        isSignal = config.has_option(section, 'Signal')
        mcSignalSamples = eval(config.get(section,'Datas'))
        identifier = ','.join(dataSamples) + '__' + str(isSignal) + '__' + ','.join(mcSignalSamples)
        if identifier in regionsDict:
            regionsDict[identifier].append(region)
        else:
            regionsDict[identifier] = [region]

    regionGroups = [y for x,y in regionsDict.iteritems()]
    print ("REGION GROUPS:",regionGroups)

    # loop over all region group. A region group is defined to have the same data samples.
    for regionGroup in regionGroups:
        print "GROUP: ", regionGroup
        section = 'Plot:%s'%regionGroup[0]
        data = eval(config.get(section, 'Datas'))
        mc = eval(config.get('Plot_general', 'samples'))
        datasamples = info.get_samples(data)
        mcsamples = info.get_samples(mc)
        samples = mcsamples+datasamples

        samplesListToRun = [x for x in samplesList if len(x) > 0]

        for sample in samples:
            if sample.identifier in samplesListToRun or len(samplesListToRun) < 1:
                print " SAMPLE",sample
                print " id",sample.identifier

                # split merging proces for chunk of files
                files = getfilelist(sample.identifier)
                files_per_job = sample.mergeCachingSize
                files_split = [files[x:x+files_per_job] for x in xrange(0, len(files), files_per_job)]
                counter_local = 0
                for files_sublist in files_split:
                    print "  SUBMIT:", len(files_sublist), " files"
                    print "  PART:", counter_local

                    repDict['additional'] = 'MERGECACHING2'+'_'+str(counter_local)+'__'+str(sample)
                    jobName = ','.join(regionGroup)

                    files_sublist_filtered = []
                    for filename in files_sublist:
                        if filename.split('/')[-1] not in sample.skipParts:
                            files_sublist_filtered.append(filename)
                        else:
                            print ('WARNING: the tree part '+filename+' will be excluded from merge, since it is in the skipParts section.')

                    globalFilesSubmitted += 1
                    print "  --->submit"
                    filelistString = ';'.join(files_sublist_filtered)
                    # necessary due to limits on passed arguments size
                    if files_per_job > 400:
                        lenBefore = len(filelistString)
                        filelistString = 'base64:' + base64.b64encode(zlib.compress(filelistString, 9))
                        lenAfter = len(filelistString)
                        print ('used base64(zlib(.)) to compress from ', lenBefore, ' to ', lenAfter, ' bytes.')
                    submitsinglefile(job=jobName, repDict=repDict, file=filelistString, run_locally=run_locally, counter_local=counter_local, Plot='', resubmit=False)
                    counter_local = counter_local + 1

#print 'item is', item
#signals = eval('['+config.get('dc:%s'%item,'signal')+']')
#backgrounds = eval(config.get('LimitGeneral','BKG'))
#all_samples = info.get_samples(signals+backgrounds)
#data_sample_names = eval(config.get('dc:%s'%item,'data'))
#data_samples = info.get_samples(data_sample_names)
#samples = all_samples+data_samples
#for sample in samples:
#    print 'sample is', sample
#    repDict['additional'] = 'CACHING'+'__'+str(sample)
#    submit(item,repDict)

#mergecaching:     Caching for ploting step
#mergesubcaching:  Caching for train step
#mergesyscaching:  Caching for dc step
if opts.task == 'mergecaching' or opts.task == 'mergesubcaching' or opts.task == 'mergesyscaching':
    Plot_vars = [x.strip() for x in (config.get('Plot_general','List')).split(',')]
    train_list = [x.strip() for x in (config.get('MVALists','List_for_submitscript')).split(',')]
    if opts.task == 'mergecaching': region_list = Plot_vars
    elif opts.task == 'mergesubcaching': region_list = train_list
    elif opts.task == 'mergesyscaching': region_list = [x.strip() for x in (config.get('LimitGeneral','List')).split(',')]
    #for region in Plot_vars:
    for region in region_list:
        if opts.task == 'mergecaching':
            section='Plot:%s'%region
            print 'section is', section
            samplesinfo=config.get('Directories','samplesinfo')
            data = eval(config.get(section,'Datas'))
            mc = eval(config.get('Plot_general','samples'))
            info = ParseInfo(samplesinfo,path)
            print info
            datasamples = info.get_samples(data)
            mcsamples = info.get_samples(mc)
            samples = mcsamples+datasamples
        elif opts.task == 'mergesubcaching':
            print 'region is', region
            path = config.get("Directories","samplepath")
            samplesinfo=config.get('Directories','samplesinfo')
            info = ParseInfo(samplesinfo,path)
            signals = eval(config.get(region,'signals'))
            backgrounds = eval(config.get(region,'backgrounds'))
            samples = info.get_samples(signals+backgrounds)
        elif opts.task == 'mergesyscaching':
            print 'region is', region
            #signals = eval('['+config.get('dc:%s'%region,'signal')+']')
            signals = eval(config.get('dc:%s'%region,'signal'))
            #print 'signals are', signals
            backgrounds = eval(config.get('dc:%s'%region,'background'))
            #print 'background are', backgrounds
            #backgrounds = eval(config.get('Plot_general','allBKG'))
            all_samples = info.get_samples(signals+backgrounds)
            #print 'all_samples are', all_samples
            #sys.exit()
            data_sample_names = eval(config.get('dc:%s'%region,'data'))
            data_samples = info.get_samples(data_sample_names)
            samples = all_samples+data_samples

            ##check if all samples are included
            #print 'samples are'
            #for sample_ in samples:
            #    print sample_.FullName
            #sys.exit()

        for sample in samples:
            print "SAMPLE",sample
            print "id",sample.identifier

            files = getfilelist(sample.identifier)
            files_per_job = sample.mergeCachingSize
            
            # test!
            files_split = [files[x:x+files_per_job] for x in xrange(0, len(files), files_per_job)]
            counter_local = 0
            for files_sublist in files_split:
                print "  SUBMIT:", len(files_sublist), " files"
                #for file in files_sublist:
                #    print "    ",file
                print "  PART:", counter_local

                repDict['additional'] = 'MERGECACHING'+'_'+str(counter_local)+'__'+str(sample)

                if opts.task == 'mergecaching' and config.has_option(section,'subcut'):
                    subcut = eval(config.get(section,'subcut'))
                    print 'subcut is', subcut

                    for cutvar, CUTBIN in subcut.iteritems():
                        print 'cutvar is', cutvar
                        for cutbins in CUTBIN:
                            print 'cutbins is', cutbins
                            cut_ = 'CUTBIN_%s__%g__%g'%(cutvar,cutbins[0], cutbins[1])
                            print 'cut_ is', cut_
                            repDict['additional'] += cut_

                print "  REPDICT:",repDict['additional']

                #Retrieve the caching cuts (methode depends on the task)
                jobName = region # todo: add sample name
                if opts.task == 'mergecaching':
                    if config.has_option('Cuts',region):
                        cut = config.get('Cuts',region)
                    elif config.has_option(section, 'Datacut'):
                        cut = config.get(section, 'Datacut')
                    else:
                        cut = None
                elif opts.task == 'mergesubcaching':
                    cutregion = config.get(region,"treeCut")
                    print 'cutregion is', cutregion
                    if config.has_option('Cuts',cutregion):
                        cut = config.get('Cuts',cutregion)
                    else:
                        cut = None
                elif opts.task == 'mergesyscaching':
                    #initalise variables to check hash
                    RCut = config.get('dc:%s'%region,'cut')
                    treecut = config.get('Cuts',RCut)
                    isdata = False
                    if sample in data_samples:
                        isdata = True
                    print 'isdata is', isdata
                    minCut = return_splitcaching_hash(treecut,isdata)

                    #Old
                    #print 'configs is', configs
                    #check_cut_command = 'python workspace_datacard.py'
                    #for conf in configs:
                    #    check_cut_command += ' -C %s'%conf
                    #check_cut_command += ' -V %s'%region
                    #check_cut_command += ' -R True'
                    #check_cut_command += ' -f \'\''
                    #print 'check_cut_command is', check_cut_command

                    ##minCut = 'dummy'

                    ##sys.exit()

                    #proc = subprocess.Popen([check_cut_command],shell = True, stdout=subprocess.PIPE)
                    #cut_string = proc.communicate()[0]
                    #minCut = cut_string.split('For submission check: The cut string is')[-1].split('End submission string')[-2]
                    #print 'cut_string is', minCut

                    #if minCut == minCut2:
                    #    print 'minCuts are equal'
                    #else:
                    #    print 'ERROR: minCuts are not equal !'

                    #print '====================='
                    #print 'minCut is', minCut
                    #print '====================='
                    #print 'minCut2 is', minCut2
                    #print '====================='

                    #sys.exit()

                    #os.system(check_cut_command)
                    #sys.exit()

                if not opts.task == 'mergesyscaching':
                    minCut = '(%s)'%cut.replace(' ','')
                #if sample.subsample:
                #    minCut = '((%s)&(%s))' %(minCut,sample.subcut)
                hash = hashlib.sha224('%s_%s_split%d' %(sample,minCut,sample.mergeCachingSize)).hexdigest()
                #if len(minCut) < 2000:
                print "  CUT:", minCut
                if len('%s_%s_split%d' %(sample,minCut,sample.mergeCachingSize)) < 2000:
                    print "  HASH-STRING:",'%s_%s_split%d' %(sample,minCut,sample.mergeCachingSize)
                print "  HASH:", hash


                files_sublist_filtered = []
                for filename in files_sublist:
                    if filename.split('/')[-1] not in sample.skipParts:
                        files_sublist_filtered.append(filename)
                    else:
                        print ('WARNING: the tree part '+filename+' will be excluded from merge, since it is in the skipParts section.')

                bool_submit = True
                if tmp_file_exists(hash, counter_local):
                    print "  --->exists"

                    if opts.task == 'mergesubcaching':
                        #Note: those should be exaclty the same cut string as in train.py, otherwise jobs are not skipped correctly
                        MVAcut_train = '!((evt%2)==0 || isData)'
                        MVAcut_eval = '((evt%2)==0 || isData)'
                        if subcut_tmpfile_exists(hash,counter_local,MVAcut_train) and subcut_tmpfile_exists(hash,counter_local,MVAcut_eval):
                            print "subcached  --->exists"
                            bool_submit = False
                            globalFilesSkipped += 1
                    else:
                        globalFilesSkipped += 1
                        bool_submit = False

                if bool_submit:
                    print 'SUBMITED'
                    globalFilesSubmitted += 1
                    print "  --->submit"
                    filelistString = ';'.join(files_sublist_filtered)
                    # necessary due to limits on passed arguments size
                    if files_per_job > 400:
                        lenBefore = len(filelistString)
                        filelistString = 'base64:' + base64.b64encode(zlib.compress(filelistString, 9))
                        lenAfter = len(filelistString)
                        #print ('used base64(zlib(.)) to compress from ', lenBefore, ' to ', lenAfter, ' bytes.')
                    submitsinglefile(job=jobName, repDict=repDict, file=filelistString, run_locally=run_locally, counter_local=counter_local, Plot=region, resubmit=False)
                else:
                    print 'SKIPED !'
                    #print 'TRAINCUT',subcut_tmpfile_exists(hash,counter,MVAcut_train)
                    #print 'EVALCUT', subcut_tmpfile_exists(hash,counter,MVAcut_eval)
                    #print ''
                counter_local = counter_local + 1

                #break # only first bunch of n files
            #break # only first sample
        #break # only first plot region
    print "skipped:", globalFilesSkipped
    print "submitted:", globalFilesSubmitted

if opts.task == 'splitcaching':
    Plot_vars= [x.strip() for x in (config.get('Plot_general','List')).split(',')]
    repDict['queue'] = 'all.q'
    for region in Plot_vars:
        section='Plot:%s'%region
        print 'section is', section
        samplesinfo=config.get('Directories','samplesinfo')
        data = eval(config.get(section,'Datas'))
        mc = eval(config.get('Plot_general','samples'))
        info = ParseInfo(samplesinfo,path)
        datasamples = info.get_samples(data)
        mcsamples = info.get_samples(mc)
        samples= mcsamples+datasamples
        for sample in samples:
            #include caching parameter such that only one sample is processed
            repDict['additional'] = 'CACHING'+'__'+str(sample)
            if not config.has_option(section, 'subcut'):
                print 'No subcut for the plot region', region
                submit(region,repDict)
                continue
            subcut = eval(config.get(section,'subcut'))
            print 'subcut is', subcut
            for cutvar, CUTBIN in subcut.iteritems():
                print 'cutvar is', cutvar
                #cutbin_first = CUTBIN[0]
                for cutbins in CUTBIN:
                    print 'cutbins is', cutbins
                    cut_ = 'CUTBIN_%s__%g__%g'%(cutvar,cutbins[0], cutbins[1])
                    print 'cut_ is', cut_
                    #Need to propagate the cutbin param
                    repDict['additional'] += cut_
                    submit(region,repDict)

if opts.task == 'splitcachingdc':
    DC_vars= [x.strip() for x in (config.get('LimitGeneral','List')).split(',')]
    repDict['queue'] = 'all.q'
    #Loop over all the dcs
    for item in DC_vars:
        #get all the samples list
        print 'item is', item 
        signals = eval('['+config.get('dc:%s'%item,'signal')+']')
        #backgrounds = eval(config.get('LimitGeneral','BKG'))
        backgrounds = eval(config.get('dc:%s'%item,'background'))
        all_samples = info.get_samples(signals+backgrounds)
        data_sample_names = eval(config.get('dc:%s'%item,'data'))
        data_samples = info.get_samples(data_sample_names)
        samples = all_samples+data_samples
        for sample in samples:
            print 'sample is', sample
            repDict['additional'] = 'CACHING'+'__'+str(sample)
            submit(item,repDict)
        #submit(item,repDict)
   ######## 
        #section='Plot:%s'%item
        #print 'section is', section
        #samplesinfo=config.get('Directories','samplesinfo')
        #data = eval(config.get(section,'Datas'))
        #mc = eval(config.get('Plot_general','samples'))
        #info = ParseInfo(samplesinfo,path)
        #datasamples = info.get_samples(data)
        #mcsamples = info.get_samples(mc)
        #samples= mcsamples+datasamples
        #for sample in samples:
        #    #include caching parameter such that only one sample is processed
        #    repDict['additional'] = 'CACHING'+'__'+str(sample)
        #    if not config.has_option(section, 'subcut'):
        #        print 'No subcut for the plot item', item
        #        submit(item,repDict)
        #        continue
        #    subcut = eval(config.get(section,'subcut'))
        #    print 'subcut is', subcut
        #    for cutvar, CUTBIN in subcut.iteritems():
        #        print 'cutvar is', cutvar
        #        for cutbins in CUTBIN:
        #            print 'cutbins is', cutbins
        #            cut_ = 'CUTBIN_%s__%g__%g'%(cutvar,cutbins[0], cutbins[1])
        #            print 'cut_ is', cut_
        #            repDict['additional'] += cut_
        #            submit(item,repDict)


if opts.task == 'trainReg':
    repDict['queue'] = 'all.q'
    submit('trainReg',repDict)


elif opts.task == 'dc' or opts.task == 'mergesyscachingdc'  or opts.task == 'mergesyscachingdcsplit' or opts.task == 'mergesyscachingdcmerge':
    repDict['queue'] = 'all.q'
    for item in DC_vars:
        # item here contains the dc name
        if opts.task == 'mergesyscachingdcsplit':
            split_factor = eval(config.get('LimitGeneral','split_factor'))
            for i in range(0,split_factor+4):
                 #if i != 34: continue
                 #if i == 3: continue
                 #if i != 3: continue
                 repDict['additional'] = 'SPLIT'+'_'+str(i)
                 submit(item,repDict)
        elif opts.task == 'mergesyscachingdcmerge':
            repDict['additional'] = 'DCMERGE'
            submit(item,repDict)
        else:
            submit(item,repDict)


elif opts.task == 'prep':
    if ( opts.samples == ""):
        path = config.get("Directories","PREPin")
        info = ParseInfo(samplesinfo,path)
        for job in info:
            submit(job.name,repDict)
    else:
        for sample in samplesList:
            submit(sample,repDict)


elif opts.task == 'singleprep' or opts.task == 'singlesys' or opts.task == 'singleeval' or opts.task == 'singleplot' or opts.task == 'mergesingleprep' or opts.task == 'mergesinglesys' or opts.task == 'mergesingleeval' or opts.task == 'mergesingleplot':
    if opts.task == 'singleprep' or opts.task == 'mergesingleprep':
        path = config.get("Directories","PREPin")
    elif opts.task == 'singlesys' or opts.task == 'mergesinglesys':
        path = config.get("Directories","SYSin")
    elif opts.task == 'singleeval' or opts.task == 'mergesingleeval':
        path = config.get("Directories","MVAin")
    elif opts.task == 'singleplot' or opts.task == 'mergesingleplot':
        path = config.get("Directories","plottingSamples")
    info = ParseInfo(samplesinfo,path)
    sample_list = {}
    if ( samplesList == [''] ):
        for job in info:
            sample_list[job.identifier] = [job.name] if not sample_list.has_key(job.identifier) else sample_list[job.identifier] + [job.name]
    else:
        for job in info:
            if job.identifier in samplesList:
                sample_list[job.identifier] = [job.name] if not sample_list.has_key(job.identifier) else sample_list[job.identifier] + [job.name]

    for item in Plot_vars:
        if opts.task == 'singleplot':
            section='Plot:%s'%item
            data = eval(config.get(section,'Datas'))# read the data corresponding to each CR (section)
            mc = eval(config.get('Plot_general','samples'))# read the list of mc samples
            # print 'data',data
            # print 'mc',mc
        for sample, sampleplot in sample_list.iteritems():
            print 'sample',sample
            if sample == '': continue
            if opts.task == 'singleprep' or opts.task == 'singlesys' or opts.task == 'singleeval' or opts.task == 'singleplot':
                files = getfilelist(sample)
                files_per_job = int(opts.nevents_split_nfiles_single) if int(opts.nevents_split_nfiles_single) > 0 else int(config.get("Configuration","files_per_job"))
                files_split=[files[x:x+files_per_job] for x in xrange(0, len(files), files_per_job)]
                files_split = [';'.join(sublist) for sublist in files_split]
                counter_local = 0
                if opts.task == 'singleplot':
                    if set(sampleplot).isdisjoint(data+mc):
                        print 'not included in plotting region',item
                        continue
                for files_sublist in files_split:
                    submitsinglefile(sample,repDict,files_sublist,run_locally,counter_local,item)
                    counter_local = counter_local + 1
            elif opts.task == 'mergesingleprep' or opts.task == 'mergesinglesys' or opts.task == 'mergesingleeval' or opts.task == 'mergesingleplot':
                mergesubmitsinglefile(sample,repDict,run_locally,item)


elif opts.task == 'checksingleprep' or opts.task == 'checksinglesys' or opts.task == 'checksingleeval' or opts.task == 'checksingleplot':
    if ( opts.samples == ""):
        if opts.task == 'checksingleprep':
            path = config.get("Directories","PREPin")
        elif opts.task == 'checksinglesys':
            path = config.get("Directories","SYSin")
        elif opts.task == 'checksingleeval':
            path = config.get("Directories","MVAin")
        elif opts.task == 'checksingleplot':
            path = config.get("Directories","plottingSamples")
        info = ParseInfo(samplesinfo,path)
        sample_list = []
        for job in info:
            sample_list.append(job.identifier)
        sample_list = set(sample_list)
    else:
        sample_list = set(samplesList)

    counter_local = 0
    for item in Plot_vars:
        checksinglestep(repDict,run_locally,counter_local,item)
        counter_local = counter_local + 1

# ADD SYSTEMATIC UNCERTAINTIES AND ADDITIONAL HIGHER LEVEL VARIABLES TO THE TREES
elif opts.task == 'sys' or opts.task == 'syseval':
    path = config.get("Directories","SYSin")
    info = ParseInfo(samplesinfo,path)
    if opts.samples == "":
        for job in info:
            if (job.subsample):
                continue # avoid multiple submissions form subsamples
            # TO FIX FOR SPLITTED SAMPLE
            submit(job.name,repDict)
    else:
        for sample in samplesList:
            submit(sample,repDict)


# EVALUATION OF EVENT BY EVENT BDT SCORE
elif opts.task == 'eval':
    repDict['queue'] = 'long.q'
    path = config.get("Directories","MVAin")
    info = ParseInfo(samplesinfo,path)
    if opts.samples == "":
        for job in info:
            if (job.subsample):
                continue # avoid multiple submissions from subsamples
            if(info.checkSplittedSampleName(job.identifier)): # if multiple entries for one name  (splitted samples) use the identifier to submit
                print '@INFO: Splitted samples: submit through identifier'
                submit(job.identifier,repDict)
            else: submit(job.name,repDict)
    else:
        for sample in samplesList:
            print sample
            submit(sample,repDict)


# POSSIBILITY TO SPLIT SINGLE MERGED FILES IN SUBFILES
# IN PRINCIPLE USEFUL BUT NOT USED ANYMORE AS THE LOGIC CHANGED (I.E. DON'T MERGE FILES)
elif( opts.task == 'split' ):
    path = config.get("Directories","SPLITin")
    repDict['job_id']= int(opts.nevents_split_nfiles_single) if int(opts.nevents_split_nfiles_single) > 0 else 100000
    info = ParseInfo(samplesinfo,path)
    if ( opts.samples == "" ):
        for job in info:
            if (job.subsample): continue # avoid multiple submissions from subsamples
            submit(job.name,repDict)
    else:
        for sample in samplesList:
            submit(sample,repDict)


# BDT optimisation
elif opts.task == 'mva_opt':
    train_list = [x.strip() for x in config.get('MVALists','List_for_submitscript').split(',')]
    print train_list
    for item in train_list:
        total_number_of_steps=1
        setting = ''
        optimizationParameters = [x.strip() for x in config.get('Optimisation','parameters').split(',')]
        for par in optimizationParameters:
            scan_par=eval(config.get('Optimisation',par))
            setting+=par+'='+str(scan_par[0])+':'
            if len(scan_par) > 1 and scan_par[2] != 0:
                total_number_of_steps+=scan_par[2]
        repDict['additional']='OPT__mainpar'
        #item=config.get('Optimisation','training')
        submit(item,repDict,False)
        main_setting=setting
        # Scanning all the parameters found in the training config in the Optimisation sector
        optimizationParameters = [x.strip() for x in config.get('Optimisation','parameters').split(',')]
        for par in optimizationParameters:
            scan_par=eval(config.get('Optimisation',par))
            if len(scan_par) > 1 and scan_par[2] != 0:
                for step in range(scan_par[2]):
                    value = (scan_par[0])+((1+step)*(scan_par[1]-scan_par[0])/scan_par[2])
                    #setting=re.sub(par+'.*?:',par+'='+str(value)+':',main_setting)
                    print 'settings is', setting
                    repDict['additional']='OPT__'+par+'__'+str(value)
                    print 'additional is', 'OPT__'+par+'__'+str(value)
                    submit(item,repDict,False)

elif opts.task == 'mva_opt_eval':
    #
    #This step evaluate the BDT produced by mva_opt.
    #

    #Read the config
    repDict['queue'] = 'long.q'
    path = config.get("Directories","MVAin")
    repDict['job_id']=config.get('Optimisation','training')
    factoryname=config.get('factory','factoryname')
    MVAdir=config.get('Directories','vhbbpath')+'/python/weights/'
    #Read weights from optimisaiton config, store the in a list (copied from mva_opt)
    total_number_of_steps=1
    setting = ''
    optimizationParameters = [x.strip() for x in config.get('Optimisation','parameters').split(',')]
    for par in optimizationParameters:
        scan_par=eval(config.get('Optimisation',par))
        setting+=par+'='+str(scan_par[0])+':'
        if len(scan_par) > 1 and scan_par[2] != 0:
            total_number_of_steps+=scan_par[2]
    repDict['additional']=setting
    repDict['job_id']=config.get('Optimisation','training')
    main_setting=setting
    config_weights_list = ['OPT_main_set']
    for par in (config.get('Optimisation','parameters').split(',')):
        scan_par=eval(config.get('Optimisation',par))
        if len(scan_par) > 1 and scan_par[2] != 0:
            for step in range(scan_par[2]):
                value = (scan_par[0])+((1+step)*(scan_par[1]-scan_par[0])/scan_par[2])
                setting=re.sub(par+'.*?:',par+'='+str(value)+':',main_setting)
                config_weights_list.append('OPT_'+par+str(value))
    #List all the weights produced from the optimisation, read from the weight directory. return weights_list
    weights = ''
    for cw in config_weights_list:
        for w in os.listdir(MVAdir):
            w = w.replace(factoryname+'_','')
            w = w.replace('.root','')
            if not w == cw: continue
            weights += w + ','
    if weights[-1] == ',': weights = weights[:-1]#remove , at the end of the list
    #submit the jobs
    info = ParseInfo(samplesinfo,path)
    repDict['additional']=weights
    print 'The optimisation weights are', weights
    if opts.samples == "":
        for job in info:
            if (job.subsample):
                continue # avoid multiple submissions from subsamples
            if(info.checkSplittedSampleName(job.identifier)): # if multiple entries for one name  (splitted samples) use the identifier to submit
                print '@INFO: Splitted samples: submit through identifier'
                submit(job.identifier,repDict)
            else: submit(job.name,repDict)
    else:
        for sample in samplesList:
            print sample
            submit(sample,repDict)

#Work in progress...
elif opts.task == 'mva_opt_dc':
    total_number_of_steps=1
    setting = ''
    for par in (config.get('Optimisation','parameters').split(',')):
        scan_par=eval(config.get('Optimisation',par))
        setting+=par+'='+str(scan_par[0])+':'
        if len(scan_par) > 1 and scan_par[2] != 0:
            total_number_of_steps+=scan_par[2]
    print setting
    repDict['additional']='OPT_main_set'
    dc = config.get('Optimisation','dc')
    #Still need to launch main
    submit(dc,repDict,False)
    main_setting=setting
    # Scanning all the parameters found in the training config in the Optimisation sector
    for par in (config.get('Optimisation','parameters').split(',')):
        scan_par=eval(config.get('Optimisation',par))
        print par
        if len(scan_par) > 1 and scan_par[2] != 0:
            for step in range(scan_par[2]):
                value = (scan_par[0])+((1+step)*(scan_par[1]-scan_par[0])/scan_par[2])
                print value
                repDict['additional']='OPT_'+par+str(value)
                submit(dc,repDict,False)
                print setting



if (run_locally == 'False') and ('check' not in opts.task):
    print 'list_submitted_singlejobs',list_submitted_singlejobs.keys()
    running_jobs = ['']
    finished_jobs_marked_ok = []
    jobs_failed_5times = []
    finished = []
    completed_dataset = []
    while len(running_jobs)>0 and len(jobs_failed_5times)+len(finished_jobs_marked_ok)<(len(running_jobs)+len(finished)):
        running_jobs = os.popen('./myutils/qstat.py').read()
        time_sec = 60
        # time_sec = 1
        print 'waiting',time_sec,'seconds before to proceed'
        time.sleep(time_sec)

        #os.system('qstat')
        # if (opts.philipp_love_progress_bars):
        # os.system('./myutils/qstat.py')
        running_jobs = os.popen('./myutils/qstat.py').read()
        print '\n'+str(datetime.datetime.now()).split('.')[0]+' - running_jobs:\n',running_jobs,
        running_jobs = running_jobs.split('\n')
        # jobs_statuses = [job.split('\t') for job in running_jobs if job]
        jobs_statuses = [job.replace('\t','').split()[3] for job in running_jobs if job]
        running_jobs = [job.replace('\t','').split()[2] for job in running_jobs if job]
        # print 'running_jobs:\n',running_jobs
        # jobs_statuses = [job for job in jobs_statuses if job]
        # print 'jobs_statuses:\n',jobs_statuses
        # running_jobs = ['ZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1_LucaZllHbb13TeVsingleprep_2']

        finished = [singlejob for singlejob in list_submitted_singlejobs.keys() if (singlejob not in running_jobs) and (singlejob not in finished_jobs_marked_ok) and (singlejob not in jobs_failed_5times)]

        # print 'finished jobs marked ok',finished_jobs_marked_ok
        print 'finished jobs to be checked',finished
        print 'finished jobs marked as permanently failed',jobs_failed_5times

        print 'number of jobs: total',len(running_jobs)+len(finished_jobs_marked_ok)+len(finished)+len(jobs_failed_5times),
        print '---> failed permanently:',len(jobs_failed_5times),
        print '---> running:',jobs_statuses.count("r"),
        print '---> waiting:',jobs_statuses.count("qw"),
        print '---> marked ok:',len(finished_jobs_marked_ok),
        print '---> finished to be checked:',len(finished)

        counter_finished = 1
        for job in finished:
            # print '\nPlot_vars',Plot_vars
            for item in Plot_vars:
                print '\njob in finished',counter_finished,'of',len(finished),':',job
                counter_finished = counter_finished + 1
                # print 'filelist',list_submitted_singlejobs[job][0]
                counter_local = job.rsplit('_',1)[len(job.rsplit('_',1))-1]
                # print 'counter_local',counter_local
                replace_string = '_%(en)s%(task)s' %repDict
                # print 'replace_string',replace_string
                # sample = job.replace('_'+counter_local,'').replace(replace_string,'')
                sample = job.replace(replace_string,'')
                sample = (sample[::-1].replace(('_'+counter_local)[::-1], '', 1))[::-1]
                print 'sample',sample
                needtoresubmit = 0
                if sample not in completed_dataset:
                    needtoresubmit = checksinglestep(repDict,run_locally,counter_local,item,list_submitted_singlejobs[job][0],sample)
                print 'needtoresubmit',needtoresubmit
                if needtoresubmit == 1 :
                    if int(list_submitted_singlejobs[job][1]) < 6 :
                      list_submitted_singlejobs[job][1] = list_submitted_singlejobs[job][1] + 1
                      print 'submitting for the',list_submitted_singlejobs[job][1],'time'
                      submitsinglefile(sample,repDict,list_submitted_singlejobs[job][0],run_locally,counter_local,item,True)
                      running_jobs.append(sample)
                    else:
                      print 'job failed 5 resubmission, marking as PERMANENTLY FAILED'
                      jobs_failed_5times.append(job)
                else:
                    if needtoresubmit == 10 :
                        completed_dataset.append(sample)
                    finished_jobs_marked_ok.append(job)
        running_jobs1 = os.popen('./myutils/qstat.py').read()
        running_jobs1 = filter(None, running_jobs1.split('\n'))
        running_jobs.append(running_jobs1)
        print '\n'+str(datetime.datetime.now()).split('.')[0]
    print 'number of jobs: total',len(finished_jobs_marked_ok)+len(jobs_failed_5times),
    print '---> marked ok:',len(finished_jobs_marked_ok),
    print '---> failed permanently:\n',jobs_failed_5times

