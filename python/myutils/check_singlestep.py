#! /usr/bin/env python
import ROOT,sys,os,subprocess,random,string,hashlib
ROOT.gROOT.SetBatch(True)
from printcolor import printc
import pickle
import sys
from optparse import OptionParser
from BetterConfigParser import BetterConfigParser
from sample_parser import ParseInfo
import StackMaker, HistoMaker

if __name__ == "__main__":

    print 'start check_singlestep.py'

    argv = sys.argv

    #get files info from config
    parser = OptionParser()
    parser.add_option("-C", "--config", dest="config", default=[], action="append",
                          help="directory config")
    parser.add_option("-S", "--samples", dest="names", default="",
                                  help="samples you want to run on")
    parser.add_option("-R", "--region", dest="region", default="",
                                  help="region to plot")

    parser.add_option("-t", "--task", dest="task", default="",
                                  help="task (prep, sys, eval, plot) to be checked")

    (opts, args) = parser.parse_args(argv)

    config = BetterConfigParser()
    config.read(opts.config)

    samplesinfo=config.get('Directories','samplesinfo')
    sampleconf = BetterConfigParser()
    sampleconf.read(samplesinfo)

    if opts.task == 'checksingleprep':
        pathOUT_orig = config.get('Directories','PREPout')
    elif opts.task == 'checksinglesys':
        pathOUT_orig = config.get('Directories','SYSout')
    elif opts.task == 'checksingleeval':
        pathOUT_orig = config.get('Directories','MVAout')
    elif opts.task == 'checksingleplot':
        pathOUT_orig = config.get('Directories','plottingSamples')

    info = ParseInfo(samplesinfo,pathOUT_orig)
    pathOUT_orig = pathOUT_orig.replace('gsidcap://t3se01.psi.ch:22128/','').replace('dcap://t3se01.psi.ch:22125/','').replace('root://t3dcachedb03.psi.ch:1094/','')
    print "opts.task",opts.task

    # print 'opts.region',opts.region
    # if opts.region:
        # region = opts.region
        # print 'evaluating cuts for region',region
        # section='Plot:%s'%region
        # vars = (config.get(section, 'vars')).split(',')#get the variables to be ploted in each region
        # print 'vars',vars
        # SignalRegion = False
        # if config.has_option(section,'Signal'):
            # # mc.append(config.get(section,'Signal'))
            # SignalRegion = True
        # #GETALL AT ONCE
        # options = []
        # Stacks = []
        # #print "Start Loop over the list of variables(to fill the StackMaker )" print "==============================================================\n"
        # for i in range(len(vars)):# loop over the list of variables to be ploted in each reagion
            # #print "The variable is ", vars[i], "\n"
            # Stacks.append(StackMaker.StackMaker(config,vars[i],region,SignalRegion))# defined in myutils DoubleStackMaker. The StackMaker merge together all the informations necessary to perform the plot (plot region, variables, samples and signal region ). "options" contains the variables information, including the cuts.
            # options.append(Stacks[i].options)

        # print options
        # exit(1)

    dataset_missing_files = []
    dataset_identifiers = []
    # print "info:",info
    for job in info:
        dataset_identifiers.append(job.identifier)
    dataset_identifiers = set(dataset_identifiers)
    for identifier in dataset_identifiers:
        # print identifier
        # identifier=opts.names.split(',')[0]
        print "identifier:",identifier
        pathOUT = pathOUT_orig+'/'+identifier
        samplefiles = config.get('Directories','samplefiles')
        filenames = open(samplefiles+'/'+identifier+'.txt').readlines()
        print 'number of files on DAS:',len(filenames),filenames[0]

        # print 'pathOUT', pathOUT
        # print('ls '+pathOUT+'/*.root |wc -l')
        nFilesInPathOut = int(os.popen('ls '+pathOUT+'/*.root |wc -l').read())
        firstfileInPathOut = os.popen('ls '+pathOUT+'/*.root |head -n 1').read()
        print '    --->>    number of files produced by '+opts.task+':',nFilesInPathOut,firstfileInPathOut[0]

        if len(filenames) == int(nFilesInPathOut):
            print 'ALL FILES CORRECTLY PROCESSED BY '+opts.task+'\n'
            # sys.exit(0)
        else:
            print '-------->>>>>> MISSING '+str(len(filenames)-int(nFilesInPathOut))+'/'+str(len(filenames))+' FILES IN THE '+opts.task+' TASK FOR THE SAMPLE '+identifier+'\n'
            # sys.exit(1)
            dataset_missing_files.append(identifier)

    print '\n\nFINAL RECAP: missing files for the following datasets:'
    print dataset_missing_files

    # # print 'end check_singlestep.py'

    # samplesinfo=config.get('Directories','samplesinfo')
    # sampleconf = BetterConfigParser()
    # sampleconf.read(samplesinfo)

    # whereToLaunch = config.get('Configuration','whereToLaunch') # USEFUL IN CASE OF SITE BY SITE OPTIONS
    # prefix=sampleconf.get('General','prefix')
    # info = ParseInfo(samplesinfo,pathIN)
    # print "samplesinfo:",samplesinfo


# def check_singlestep_def(pathIN,pathOUT,prefix,newprefix,folderName,Aprefix,Acut,config):
    # '''
    # List of variables
    # pathIN: path of the input file containing the data
    # pathOUT: path of the output files
    # prefix: "prefix" variable from "samples_nosplit.cfg"
    # newprefix: "newprefix" variable from "samples_nosplit.cfg"
    # file: sample header (as DYJetsToLL_M-50_TuneZ2Star_8TeV-madgraph-tarball)
    # Aprefix: empty string ''
    # Acut: the sample cut as defined in "samples_nosplit.cfg"
    # '''
    # print('pathIN',pathIN,'pathOUT',pathOUT,'prefix',prefix,'newprefix',newprefix,'folderName',folderName,'Aprefix',Aprefix,'Acut',Acut,'config',config)
    # # prefix = theHash
    # # newprefix = tmp_

    # print 'start check_singlestep.py'
    # print (pathIN,pathOUT,prefix,newprefix,folderName,Aprefix,Acut)
    # print "##### MERGE TREE - BEGIN ######"

    # outputfile = pathOUT+'/'+newprefix+folderName+".root"
    # if prefix != '':
        # outputfile = pathOUT+'/'+newprefix+prefix+".root"

    # print 'checking if output file exists:',outputfile
    # f = ROOT.TFile.Open(outputfile,'read')
    # if not f:
        # print "MERGED FILE DOESN'T EXIST, CREATING IT"
    # elif f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
        # print "MERGED FILE EXISTS BUT IS CORRUPTED, CREATING IT"
    # else:
        # print "MERGED FILE EXISTS AND IS NOT CORRUPTED, EXITING"
        # sys.exit()


    # t = ROOT.TFileMerger(ROOT.kFALSE)
    # __tmpPath = os.environ["TMPDIR"]
    # tmp_filename = __tmpPath+'/'+newprefix+folderName+".root "
    # if prefix != '':
        # tmp_filename = __tmpPath+'/'+newprefix+prefix+".root"
    # print 'tmp_filename',tmp_filename
    # # print 't.OutputFile('+tmp_filename+',"RECREATE")'
    # # t.OutputFile(tmp_filename, "RECREATE")
    # outputFolder = "%s/%s/" %(pathOUT,folderName)
    # print 'outputFolder is', outputFolder
    # # command = 'hadd -f -k -O
    # # command = 'hadd -f '+tmp_filename+' '
    # allFiles = []
    # for file in os.listdir(outputFolder.replace('root://t3dcachedb03.psi.ch:1094','').replace('gsidcap://t3se01.psi.ch:22128/','').replace('dcap://t3se01.psi.ch:22125/','')):
        # if file.startswith('tree') and ( prefix == '' or Aprefix in file):
            # allFiles.append(outputFolder+file)
            # # command = command+' '+outputFolder+file
            # # print 't.AddFile('+outputFolder+file+')'
            # # t.AddFile(outputFolder+file)
    # print 'len(allFiles)',len(allFiles),'allFiles[0]',allFiles[0]
    # n=50
    # allFiles_chunks = [allFiles[i:i+n] for i in range(0, len(allFiles), n)]
    # print 'len(allFiles_chunks)',len(allFiles_chunks),'allFiles_chunks[0]',allFiles_chunks[0]
    # tmpfile_chunk = __tmpPath+'/'+newprefix+folderName+'_tmpfile_chunk_'
    # if prefix != '':
        # tmpfile_chunk = __tmpPath+'/'+newprefix+folderName+prefix+'_tmpfile_chunk_'
    # print 'tmpfile_chunk',tmpfile_chunk
    # counter = 0
    # for allFiles_chunk in allFiles_chunks:
        # counter = counter + 1
        # command = 'hadd -f '+tmpfile_chunk+str(counter)+'.root '
        # for file in allFiles_chunk:
            # command = command+' '+file
        # print 'merging chunk '+str(counter)
        # subprocess.call([command], shell=True)
    # command = 'hadd -f '+tmp_filename+' '
    # for ichunk in range(1,counter+1):
        # command = command+' '+tmpfile_chunk+str(ichunk)+'.root '
    # print 'start to merge all files'
    # print 'command',command
    # subprocess.call([command], shell=True)
    # # print command
    # # os.system(command)
    # # t.Merge()
    # print 'finished merging all files'

    # # DUMMY WAYS TO COPE WITH FILE COMMAND PROTOCOLS @T2-PSI...
    # del_merged = outputfile.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
    # command = 'srmrm %s' %(del_merged)
    # print command
    # subprocess.call([command], shell = True)
    # srmpathOUT = pathOUT.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
    # command = 'srmcp -2 -globus_tcp_port_range 20000,25000 file:///'+tmp_filename+' '+outputfile.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
    # print command
    # subprocess.call([command], shell=True)

    # print 'checking output file',outputfile
    # f = ROOT.TFile.Open(outputfile,'read')
    # if not f or f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
        # print 'TERREMOTO AND TRAGEDIA: THE MERGED FILE IS CORRUPTED!!! ERROR: exiting'
        # sys.exit(1)
    # f.Close()

    # command = 'rm '+tmp_filename
    # print command
    # subprocess.call([command], shell=True)
    # command = 'rm '+tmpfile_chunk+'*.root'
    # print command
    # subprocess.call([command], shell=True)

    # print "##### MERGE TREE - END ######"




