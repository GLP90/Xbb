import os
import sys
import shutil
import subprocess
import argparse

#Read input arguments



parser = argparse.ArgumentParser(description='Move plots to public webpage')
parser.add_argument('_input', nargs='*', metavar='I', help='first argument: input folder, second argument (optional) output folder. You can use --eos or --afs option to use the default path as output folder. If output folder and --eos or --afs option is set, the output folder will be appended to the default path.')
#parser.add_argument('-r', dest='region', action='store_const',
#                   const=False, default=True,  help='use automatic region list insead of default')
parser.add_argument('--server', default = None, help='other server than lxplus')
parser.add_argument('--eos', dest='webservice', action='store_const', default = False, const='eos', help='use default path with eos webserver')
parser.add_argument('--afs', dest='webservice', action='store_const', default = False, const='afs/cern.ch', help='use default path with afs webserver')
parser.add_argument('--name', default = None, help='Give a name to the new dir')

parser.add_argument('--folders', default = "region", help='how to make subfolders: <none>, <region> (default), <variable>')
parser.add_argument('--no', dest='do_outp', action='store_const',
                   const=False, default=True,  help='no copying')
parser.add_argument('--ni', dest='do_inp', action='store_const',
                   const=False, default=True,  help='no preparation of folders for each Region')
parser.add_argument('--nh', dest='ht', action='store_const',
                   const=False, default=True,  help='no htaccess file is created')

args = parser.parse_args()
#args = sys.argv[1:]
#if len(args) == 2:
#    _input = args[0]
#    _output = args[1]
#else:
#    print 'Error, need two agruments. You have provided', len(args)
#    sys.exit(1)


_input = args._input[0]
if len(args._input) > 1:
    _output = args._input[1]

else:
    _output = "/"

args.region = False
print 'Input folder is', _input
print 'Output folder is', _output

#Move all plots in corresponding subfolders

def MakeSubFolders(_input, RegionList=None):

    #I am in macro location
    #I am in Plots
    if args.name is None:
        _plotfolder = _input.split('/')[-2]
    else:
        _plotfolder = args.name
    
    if not os.path.isdir(_plotfolder):
        os.mkdir(_plotfolder)

    print 'command is','cp -r ../config ' + _plotfolder + '/'
    subprocess.call('cp -r ../config ' + _plotfolder + '/', shell = True)
    
    if args.ht:
        print 'command is','cp -r '+current_+'/.htaccess ' + _plotfolder + '/'
        subprocess.call('cp -r '+current_+'/.htaccess ' + _plotfolder + '/', shell = True)
        subprocess.call('cp -r ' + current_ + '/.htaccess ' + _plotfolder + '/config/', shell = True)
    subprocess.call('cp -r '+current_+'/index.php ' + _plotfolder + '/', shell = True)
    subprocess.call('cp -r ' + current_ + '/index.php ' + _plotfolder + '/config/', shell = True)
    FILE = os.listdir('.')

    #subprocess.call('cp -r ../config .', shell = True)
    
    #make default RegionList
    if RegionList is None:
        RegionList = []
    if not args.folders == 'none':
        for file in FILE:
               
                #skip folders in listdir
                if not os.path.isfile(file):
                    continue
                if args.folders == 'region':
                    region = file.split("__")[0]
                    region = region.replace("comp_","")
                elif args.folders == 'variable':
                    region = file.split("__")[1]
                    region = region.split(".")[0]
                if region not in RegionList:
                    RegionList.append((region,region)) 
        #print RegionList
   
    for file in FILE:
        #if not 'comp' in file: continue #Skip shape plots
        print 'file is', file
        
        #skip folders in listdir
        if not os.path.isfile(file):
            continue
        
        folder2 = None
        for name, folder in RegionList:
            if not name in file: continue
            folder2 = os.path.join(_plotfolder,folder)
            break
        if not folder2:
            if not '.pdf' in file and not '.png' in file and not '.root' in file: continue
            else:
                folder2 = _plotfolder
                #If file is not in RegionList, create folder using file prefix
            #    folder = file.split('__')[0]
            #    folder2 = os.path.join(_plotfolder,folder)

        print 'folder2 is', folder2
        if folder2:
            if not os.path.isdir(folder2):
                os.mkdir(folder2)
                #subprocess.call('cp -r ../config '+ folder2 + '/', shell = True)
                if args.ht:
                    subprocess.call('cp -r '+current_+'/.htaccess ' + folder2 + '/', shell = True)
                subprocess.call('cp -r '+current_+'/index.php ' + folder2 + '/', shell = True)
            if os.path.isfile(file):
                shutil.copy(file,folder2)
            if os.path.isfile('pdf/'+file.replace('png','pdf')):
                shutil.copy('pdf/'+file.replace('png','pdf'), folder2)
            else:
                pass
                #print 'pdf/'+file.replace('png','pdf'), 'doesn\'t exist'
            if os.path.isfile('root/'+file.replace('png','C')) :
                shutil.copy('root/'+file.replace('png','C'), folder2)
                #print 'root is here'
            else:
                pass
                #print 'root/'+file.replace('png','C'), 'doesn\'t exist'

def MoveSubFolders(_input, _output, server=None):
    if server is None:
        process = os.popen('echo $USER')
        user = process.read().strip()
        process.close()
        server = user + '@lxplus.cern.ch'
    
    if args.name is None:
        _plotfolder = _input.split('/')[-2]
    else:
        _plotfolder = args.name

    if args.webservice:
        _output = '/' + args.webservice+ '/user/' + user[0] + "/" + user + "/www" + _output
    print 'gonna lunch the command'
    copyCommand = 'scp -r ' + _plotfolder + ' ' + server + ':' + _output
    print copyCommand
    subprocess.call(copyCommand, shell = True)
    print 'that was delicious!'


#RegionList = [('Zll_CRZb_incl__','Zhf_Zll'),('Zll_CRZb_incl_lowpt__','Zhf_Zll_lowpt'),('Zll_CRZb_incl_highpt__','Zhf_Zll_highpt'),\
#              ('Zll_CRZlight__','Zlf_Zll'),('Zll_CRZlight_lowpt__','Zlf_Zll_lowpt'),('Zll_CRZlight_highpt__','Zlf_Zll_highpt'),\
#              ('Zll_CRttbar__','ttbar_Zll'),('Zll_CRttbar_lowpt__','ttbar_Zll_lowpt'),('Zll_CRttbar_highpt__','ttbar_Zll_highpt'),\
#              ('Zee_SR','SR_Zee'),('Zuu_SR','SR_Zuu'),\
#              ('Zee_CRZb_incl__','Zhf_Zee'),('Zee_CRZb_incl_lowpt__','Zhf_Zee_lowpt'),('Zee_CRZb_incl_highpt__','Zhf_Zee_highpt'),\
#              ('Zee_CRZlight__','Zlf_Zee'),('Zee_CRZlight_lowpt__','Zlf_Zee_incl_lowpt'),('Zee_CRZlight_highpt__','Zlf_Zee_incl_highpt'),\
#              ('Zee_CRttbar__','ttbar_Zee'),('Zee_CRttbar_lowpt__','ttbar_Zee_lowpt'),('Zee_CRttbar_highpt__','ttbar_Zee_highpt'),\
#              ('Zuu_CRZb_incl__','Zhf_Zuu'),('Zuu_CRZb_incl_lowpt__','Zhf_Zuu_lowpt'),('Zuu_CRZb_incl_highpt__','Zhf_Zuu_highpt'),\
#              ('Zuu_CRZlight__','Zlf_Zuu'),('Zuu_CRZlight_lowpt__','Zlf_Zuu_lowpt'),('Zuu_CRZlight_highpt__','Zlf_Zuu_highpt'),\
#              ('Zuu_CRttbar__','ttbar_Zuu'),('Zuu_CRttbar_lowpt__','ttbar_Zuu_lowpt'),('Zuu_CRttbar_highpt__','ttbar_Zuu_highpt'),\
#              ('Zee_CRZb_incl_new','Zhf_Zee_new'),('Zuu_CRZb_incl_new','Zhf_Zuu_new'),('Zll_CRZb_inclPhi2p3','Zhf_Zll_Phi2p3'),('Zll_CRZb_inclPhi2p5','Zhf_Zll_Phi2p5'),('Zll_CRZb_inclPhi2p5','Zhf_Zll_Phi2p5'),('Zll_CRZlightPhi2p3','Zlf_Zll_Phi2p3'),('Zll_CRZlightPhi2p5','Zlf_Zll_Phi2p5'),('BasicCuts_low','BasicCuts_low'),('BasicCuts_high','BasicCuts_high'),
#              ('Zll_BasicCuts','ZBasicCuts_Zll'),\
#              ('ZeeBDT_lowpt','ZSR_Zee_lowpt'),('ZeeBDT_highpt','ZSR_Zee_highpt'),('ZuuBDT_lowpt','ZSR_Zuu_lowpt'),('ZuuBDT_highpt','ZSR_Zuu_highpt'),\
#              ('ZllBDT__','ZSR_Zll'),('ZllBDT_lowpt__','ZSR_Zll_lowpt'),('ZllBDT_highpt__','ZSR_Zll_highpt'),\
#              ('all','all'),('nivf2','nivf2'),('HTL400','HLT400'),('HTL400nivf2','HTL400nivf2')\
#              ]

current_ = os.getcwd()
os.chdir(_input)
if args.do_inp:
    if args.region:
        MakeSubFolders(_input, RegionList)
    else:
        MakeSubFolders(_input)

if args.do_outp:
    MoveSubFolders(_input, _output, args.server)

