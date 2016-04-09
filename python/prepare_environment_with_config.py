#! /usr/bin/env python
import os, pickle, sys, ROOT
ROOT.gROOT.SetBatch(True)
from optparse import OptionParser
from myutils import BetterConfigParser, copytree, copytreePSI, ParseInfo
from myutils.copytreePSI import mergetreePSI
import utils

print 'start prepare_environment_with_config.py'

argv = sys.argv

#get files info from config
parser = OptionParser()
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="directory config")
parser.add_option("-S", "--samples", dest="names", default="",
                              help="samples you want to run on")
parser.add_option("-f", "--filelist", dest="filelist", default="",
                              help="list of files you want to run on")

(opts, args) = parser.parse_args(argv)

config = BetterConfigParser()
config.read(opts.config)

namelist=opts.names.split(',')
filelist=opts.filelist.split(';')
print "namelist:",namelist
# print "opts.filelist:",opts.filelist
print "len(filelist)",len(filelist),"filelist[0]:",filelist[0]

pathIN = config.get('Directories','PREPin')
pathOUT = config.get('Directories','PREPout')
samplesinfo=config.get('Directories','samplesinfo')
sampleconf = BetterConfigParser()
sampleconf.read(samplesinfo)

whereToLaunch = config.get('Configuration','whereToLaunch')
TreeCopierPSI = config.get('Configuration','TreeCopierPSI')
if TreeCopierPSI=="False":
    TreeCopierPSI = False
prefix=sampleconf.get('General','prefix')

info = ParseInfo(samplesinfo,pathIN)
print "samplesinfo:",samplesinfo
print "info:",info
for job in info:
    # print "job.name:",job.name
    if not job.name in namelist and not job.identifier in namelist:
        continue
    if job.subsample:
        continue
    if('lxplus' in whereToLaunch):
        # TreeCopier class
        utils.TreeCopier(pathIN, pathOUT, job.identifier, job.prefix, job.addtreecut)
    else:
        if TreeCopierPSI:
            samplefiles = config.get('Directories','samplefiles')
            if 'mergeall' in filelist[0]:
                mergetreePSI(samplefiles,pathOUT,prefix,job.prefix,job.identifier,'',job.addtreecut, config)
            else:
                copytreePSI(samplefiles,pathOUT,prefix,job.prefix,job.identifier,'',job.addtreecut, config, filelist)
        else:
          # copytree function
          copytree(pathIN,pathOUT,prefix,job.prefix,job.identifier,'',job.addtreecut, config)

print 'end prepare_environment_with_config.py'
