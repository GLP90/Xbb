#! /usr/bin/env python
from optparse import OptionParser
import sys
import time
import os
import shutil

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
parser.add_option("-N", "--number-of-events", dest="nevents_split", default=100000,
                      help="Number of events per file when splitting.")
parser.add_option("-P", "--philipp-love-progress-bars", dest="philipp_love_progress_bars", default=False,
                      help="If you share the love of Philipp...")
parser.add_option("-V", "--verbose", dest="verbose", action="store_true", default=False,
                      help="Activate verbose flag for debug printouts")

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


en = opts.tag

#create the list with the samples to run over
samplesList=opts.samples.split(",")
timestamp = time.asctime().replace(' ','_').replace(':','-')

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
        shutil.copyfile(item,'%s/%s/%s'%(tagDir,opts.ftag,item.strip(en)))

# DEBUG PURPOSE ONLY        
# sys.exit()

if(debugPrintOUts): print configs
config = BetterConfigParser()
config.read(configs)

logPath = config.get("Directories","logpath")
logo = open('%s/data/submit.txt' %config.get('Directories','vhbbpath')).readlines()
counter = 0
samplesinfo = config.get("Directories","samplesinfo")
whereToLaunch = config.get('Configuration','whereToLaunch')
run_locally = str(config.get("Configuration","run_locally"))
print 'whereToLaunch',whereToLaunch,'run_locally',run_locally

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
            command = 'srmmkdir srm://t3se01.psi.ch/' + _output_folder
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
        # ROOT.gSystem.CompileMacro('%s'%(scratchDir+_macro)) # THIS AS WELL...
        # print("gcc -shared -o "+library+" `root-config --glibs --libs --cflags` -fPIC "+scratchDir+_macro)
        # os.system("gcc -shared -o "+library+" `root-config --glibs --libs --cflags` -fPIC "+scratchDir+_macro)

        shutil.copyfile('/scratch/%s/%s'%(getpass.getuser(),os.path.basename(library)),library)
        print '@INFO: macro',macro,'compiled, exiting to avoid stupid ROOT crash, please resubmit!!!'
        sys.exit(1)
    os.chdir(submitDir)
        
#comment for now
print '===============================\n'
print 'Compiling the macros'
print '===============================\n'
compile_macro(config,'BTagReshaping')
compile_macro(config,'VHbbNameSpace')

#check if the logPath exist. If not exit
if( not os.path.isdir(logPath) ):
    print '@ERROR : ' + logPath + ': dir not found.'
    print '@ERROR : Create it before submitting '
    print 'Exit'
    sys.exit(-1)
    
repDict = {'en':en,'logpath':logPath,'job':'','task':opts.task,'queue': 'all.q','timestamp':timestamp,'additional':'','job_id':'','nprocesses':str(max(int(pathconfig.get('Configuration','nprocesses')),1))}
def submit(job,repDict):
    global counter
    repDict['job'] = job
    nJob = counter % len(logo)
    counter += 1
    if opts.philipp_love_progress_bars:
        repDict['name'] = '"%s"' %logo[nJob].strip()
    else:
        repDict['name'] = '%(job)s_%(en)s%(task)s' %repDict
    command = 'qsub -V -cwd -q %(queue)s -l h_vmem=6G -N %(name)s -j y -o %(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + repDict['additional']
    print "the command is ", command
    dump_config(configs,"%(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.config" %(repDict))
    subprocess.call([command], shell=True)

def submitsinglefile(job,repDict,file,run_locally,counter_local):
    global counter
    repDict['job'] = job
    nJob = counter % len(logo)
    counter += 1
    if opts.philipp_love_progress_bars:
        repDict['name'] = '"%s"' %logo[nJob].strip()
    else:
        repDict['name'] = '%(job)s_%(en)s%(task)s' %repDict
    if run_locally == 'True':
        command = 'sh runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
    else:
        command = 'qsub -V -cwd -q %(queue)s -l h_vmem=6G -N %(name)s -j y -o %(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
        command = command.replace('.out','_'+str(counter_local)+'.out')
    print "the command is ", command
    print "submitting", len(file.split(';')),'files like',file.split(';')[0]
    command = command + ' "' + str(file)+ '"'
    dump_config(configs,"%(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.config" %(repDict))
    subprocess.call([command], shell=True)
    # sys.exit()

def mergesubmitsinglefile(job,repDict,run_locally):
    global counter
    repDict['job'] = job
    nJob = counter % len(logo)
    counter += 1
    if opts.philipp_love_progress_bars:
        repDict['name'] = '"%s"' %logo[nJob].strip()
    else:
        repDict['name'] = '%(job)s_%(en)s%(task)s' %repDict
    if run_locally == 'True':
        command = 'sh runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
    else:
        command = 'qsub -V -cwd -q %(queue)s -l h_vmem=6G -N %(name)s -j y -o %(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
    command = command + ' mergeall'
    print "the command is ", command
    dump_config(configs,"%(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.config" %(repDict))
    subprocess.call([command], shell=True)

def getfilelist(job):
    pathIN = config.get('Directories','PREPin')
    pathOUT = config.get('Directories','PREPout')

    TreeCopierPSI = config.get('Configuration','TreeCopierPSI')

    samplefiles = config.get('Directories','samplefiles')
    list = filelist(samplefiles,job)
    return list

if opts.task == 'train':
    train_list = (config.get('MVALists','List_for_submitscript')).split(',')
    print train_list
    for item in train_list:
        submit(item,repDict)


if opts.task == 'dc':
    #DC_vars = config.items('Limit')
    DC_vars= (config.get('LimitGeneral','List')).split(',')
    print DC_vars

if opts.task == 'plot':
    Plot_vars= (config.get('Plot_general','List')).split(',')

if not opts.task == 'prep':
    path = config.get("Directories","samplepath")
    info = ParseInfo(samplesinfo,path)

if opts.task == 'plot': 
    repDict['queue'] = 'all.q'
    for item in Plot_vars:
        submit(item,repDict)

if opts.task == 'trainReg':
    repDict['queue'] = 'all.q'
    submit('trainReg',repDict)


elif opts.task == 'dc':
    repDict['queue'] = 'all.q'
    for item in DC_vars:
        #item here contains the dc name
        submit(item,repDict)
        #if 'ZH%s'%opts.mass in item:
        #    submit(item,repDict)

elif opts.task == 'prep':
    if ( opts.samples == ""):
        path = config.get("Directories","PREPin")
        info = ParseInfo(samplesinfo,path)
        for job in info:
            submit(job.name,repDict)
    else:
        for sample in samplesList:
            submit(sample,repDict)

elif opts.task == 'singleprep' or opts.task == 'singlesys' or opts.task == 'mergesingleprep' or opts.task == 'mergesinglesys':
    if ( opts.samples == ""):
        if opts.task == 'singleprep' or opts.task == 'mergesingleprep':
            path = config.get("Directories","PREPin")
        elif opts.task == 'singlesys' or opts.task == 'mergesinglesys':
            path = config.get("Directories","SYSin")
        info = ParseInfo(samplesinfo,path)
        sample_list = []
        for job in info:
            sample_list.append(job.identifier)
        sample_list = set(sample_list)
    else:
        sample_list = set(samplesList)

    if opts.task == 'singleprep' or opts.task == 'singlesys':
        for sample in sample_list:
            files = getfilelist(sample)
            files_per_job = int(config.get("Configuration","files_per_job"))
            files_split=[files[x:x+files_per_job] for x in xrange(0, len(files), files_per_job)]
            files_split = [';'.join(sublist) for sublist in files_split]
            counter_local = 0
            for files_sublist in files_split:
                submitsinglefile(sample,repDict,files_sublist,run_locally,counter_local)
                counter_local = counter_local + 1
    elif opts.task == 'mergesingleprep' or opts.task == 'mergesinglesys':
        for sample in sample_list:
            mergesubmitsinglefile(sample,repDict,run_locally)
            
elif opts.task == 'sys' or opts.task == 'syseval':
    path = config.get("Directories","SYSin")
    info = ParseInfo(samplesinfo,path)
    if opts.samples == "":
        for job in info:
            if (job.subsample): 
                continue #avoid multiple submissions form subsamples
            # TO FIX FOR SPLITTED SAMPLE
            submit(job.name,repDict)
    else:
        for sample in samplesList:
            submit(sample,repDict)

elif opts.task == 'eval':
    repDict['queue'] = 'long.q'
    path = config.get("Directories","MVAin")
    info = ParseInfo(samplesinfo,path)
    if opts.samples == "":
        for job in info:
            if (job.subsample): 
                continue #avoid multiple submissions from subsamples
            if(info.checkSplittedSampleName(job.identifier)): # if multiple entries for one name  (splitted samples) use the identifier to submit
                print '@INFO: Splitted samples: submit through identifier'
                submit(job.identifier,repDict)
            else: submit(job.name,repDict)
    else:
        for sample in samplesList:
            print sample
            submit(sample,repDict)


elif( opts.task == 'split' ):
    path = config.get("Directories","SPLITin")
    repDict['job_id']=opts.nevents_split
    info = ParseInfo(samplesinfo,path)
    if ( opts.samples == "" ):
        for job in info:
            if (job.subsample): continue #avoid multiple submissions from subsamples
            submit(job.name,repDict)
    else:
        for sample in samplesList:
            submit(sample,repDict)

#BDT optimisation
elif opts.task == 'mva_opt':
    total_number_of_steps=1
    setting = ''
    for par in (config.get('Optimisation','parameters').split(',')):
        scan_par=eval(config.get('Optimisation',par))
        setting+=par+'='+str(scan_par[0])+':'
        if len(scan_par) > 1 and scan_par[2] != 0:
            total_number_of_steps+=scan_par[2]
    setting=setting[:-1] # eliminate last column at the end of the setting string
    print setting
    repDict['additional']=setting
    repDict['job_id']=config.get('Optimisation','training')
    submit('OPT_main_set',repDict)
    main_setting=setting

    #Scanning all the parameters found in the training config in the Optimisation sector
    for par in (config.get('Optimisation','parameters').split(',')):
        scan_par=eval(config.get('Optimisation',par))
        print par
        if len(scan_par) > 1 and scan_par[2] != 0:
            for step in range(scan_par[2]):
                value = (scan_par[0])+((1+step)*(scan_par[1]-scan_par[0])/scan_par[2])
                print value
                setting=re.sub(par+'.*?:',par+'='+str(value)+':',main_setting)
                repDict['additional']=setting
#               repDict['job_id']=config.get('Optimisation','training')
                submit('OPT_'+par+str(value),repDict)
#               submit(config.get('Optimisation','training'),repDict)
                print setting


os.system('qstat')
if (opts.philipp_love_progress_bars):
    os.system('./qstat.py') 
