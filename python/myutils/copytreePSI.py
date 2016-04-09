import ROOT,sys,os,subprocess,random,string,hashlib
from printcolor import printc
# from copytreePSI import id_generator

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def copySingleFile(whereToLaunch,inputFile,outputFile,Acut,remove_branches):
        # print 'inputFile',inputFile
        if ('pisa' in whereToLaunch):
          input = ROOT.TFile.Open(inputFile,'read')
        else:
          input = ROOT.TFile.Open(inputFile,'read')

        if not input:
          print 'input file NOT EXISTING:',inputFile
          input.Close()
          return

        __tmpPath = os.environ["TMPDIR"]
        outputFileName = outputFile.split('/')[len(outputFile.split('/'))-1]
        print 'outputFileName',__tmpPath+'/'+outputFileName
        # output = ROOT.TFile.Open(outputFile,'create')
        output = ROOT.TFile.Open(__tmpPath+'/'+outputFileName,'recreate')
        # print "Writing file:",outputFile
        # if not output:
          # del_protocol = outputFile.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
          # del_protocol = outputFile.replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
          # del_protocol = outputFile.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
          # command = 'srmrm %s' %(del_protocol)
          # subprocess.call([command], shell=True)
          # output = ROOT.TFile.Open(outputFile,'create')

        inputTree = input.Get("tree")
        nEntries = inputTree.GetEntries()
        for branch in remove_branches:
          if branch and not branch.isspace():
            # print 'DROPPING BRANCHES LIKE',str(branch)
            inputTree.SetBranchStatus(str(branch), ROOT.kFALSE);

        output.cd()
        print '\n\t copy file: %s with cut: %s' %(inputFile,Acut)
        outputTree = inputTree.CopyTree(Acut)
        kEntries = outputTree.GetEntries()
        printc('blue','',"\t before cuts\t %s" %nEntries)
        printc('green','',"\t survived\t %s" %kEntries)
        outputTree.AutoSave()
        # input.ls()
        input.cd()
        obj = ROOT.TObject
        for key in ROOT.gDirectory.GetListOfKeys():
            input.cd()
            obj = key.ReadObj()
            if obj.GetName() == 'tree':
                continue
            output.cd()
            #print key.GetName()
            obj.Write(key.GetName())
        # output.ls()
        # print "Writing output file"
        output.Write()
        # print "Closing output file"
        output.Close()
        # print "Closing input file"
        input.Close()
        command = 'srmcp -2 -globus_tcp_port_range 20000,25000 file:///'+__tmpPath+'/'+outputFileName+' '+ outputFile.replace('root://t3dcachedb03.psi.ch:1094','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=/')
        # print command
        subprocess.call([command], shell=True)
        command = 'rm '+__tmpPath+'/'+outputFileName
        # print command
        subprocess.call([command], shell=True)

def copySingleFileOneInput(inputs):
    return copySingleFile(*inputs)

def copytreePSI(pathIN,pathOUT,prefix,newprefix,folderName,Aprefix,Acut,config,filelist):
    '''
    List of variables
    pathIN: path of the input file containing the data
    pathOUT: path of the output files
    prefix: "prefix" variable from "samples_nosplit.cfg"
    newprefix: "newprefix" variable from "samples_nosplit.cfg"
    file: sample header (as DYJetsToLL_M-50_TuneZ2Star_8TeV-madgraph-tarball)
    Aprefix: empty string ''
    Acut: the sample cut as defined in "samples_nosplit.cfg"
    '''
    print 'start copytreePSI.py'
    print (pathIN,pathOUT,prefix,newprefix,folderName,Aprefix,Acut)

    filenames = open(pathIN+'/'+folderName+'.txt').readlines() if not filelist else filelist
    print 'len(filenames)',len(filenames),filenames[0]
    # sys.exit()

    ## search the folder containing the input files
    # from os import walk
    # dirpath = ""
    # filename = ""
   # filenames = []
    inputFiles = []
    folder_prefix = ''
    print "##### COPY TREE - BEGIN ######"
    whereToLaunch = config.get('Configuration','whereToLaunch')
    remove_branches = config.get('General','remove_branches').replace("[","").replace("]","").replace("'","").split(',')
    print 'remove_branches:',remove_branches,'len(remove_branches):',len(remove_branches)

    # if('pisa' in whereToLaunch):
      # for (dirpath_, dirnames, filenames_) in walk(pathIN+'/'+folderName):
        # for filename_ in filenames_:
            # if 'root' in filename_ and not 'failed' in dirpath_:
                # inputFiles.append(dirpath_+'/'+filename_)
    # else:
    # FOLDER = pathIN+'/'+folderName
    # if FOLDER.startswith('dcap://t3se01.psi.ch:22125'):
        # FOLDER = FOLDER.replace('dcap://t3se01.psi.ch:22125','')
        # folder_prefix = 'dcap://t3se01.psi.ch:22125'
    # for (dirpath_, dirnames, filenames_) in walk(FOLDER):
    for filename_ in filenames:
        if '.root' in filename_ :
            inputFiles.append('root://xrootd-cms.infn.it//'+filename_.rstrip('\n'))

    if len(inputFiles) == 0 :
        print "No .root files found in ",pathIN+'/'+folderName
        return

    ## prepare output folder
    outputFolder = "%s/%s/" %(pathOUT,folderName)
    try:
        os.mkdir(outputFolder)
    except:
        pass
    if('PSI' in whereToLaunch):
      print 'Create the ouput folder if not existing'
      mkdir_protocol = outputFolder.replace('root://t3dcachedb03.psi.ch:1094/','')
      print 'mkdir_protocol',mkdir_protocol
      _output_folder = ''
      for _folder in mkdir_protocol.split('/'):
          #if mkdir_protocol.split('/').index(_folder) < 3: continue
          # print 'checking and/or creating folder',_output_folder
          _output_folder += '/'+_folder
          if os.path.exists(_output_folder):
              # print 'exists'
              cicciobello = 1
          else:
              # print 'does not exist'
              command = 'srmmkdir srm://t3se01.psi.ch/' + _output_folder
              subprocess.call([command], shell = True)
          # if os.path.exists(_output_folder): print 'Folder', _output_folder, 'sucessfully created'

    ## prepare a list of input(inputFile,outputFile,Acut) for the files to be processed
    inputs=[]
    filenames=[]
    for inputFile in inputFiles:
        subfolder = inputFile.split('/')[-4]
        filename = inputFile.split('/')[-1]
        filename = filename.split('_')[0]+'_'+subfolder+'_'+filename.split('_')[1]
        if filename in filenames: continue
        filenames.append(filename)
        # hash = filename.encode("hex")
        hash = hashlib.sha224(filename).hexdigest()
        # outputFile = "%s/%s/%s" %(pathOUT,folderName,filename.replace('.root','')+'_'+id_generator()+'.root')
        # print 'hash',hash
        outputFile = "%s/%s/%s" %(pathOUT,folderName,filename.replace('.root','')+'_'+str(hash)+'.root')
        # print 'inputFile',inputFile,'outputFile',outputFile
        if('PSI' in whereToLaunch):
          del_protocol = outputFile
        else:
          del_protocol = pathOUT

        del_protocol = del_protocol.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
        del_protocol = del_protocol.replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
        del_protocol = del_protocol.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
        # print "cutting ",inputFile," ---> ",outputFile

        # print 'del_protocol',del_protocol,'isfile',os.path.isfile(del_protocol.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=',''))
        if os.path.isfile(del_protocol.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=','')):
            f = ROOT.TFile.Open(outputFile,'read')
            if not f:
              print 'file is null, adding to input'
              inputs.append((whereToLaunch,inputFile,outputFile,Acut,remove_branches))
              continue
            # f.Print()
            if f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
                print 'f.GetNkeys()',f.GetNkeys(),'f.TestBit(ROOT.TFile.kRecovered)',f.TestBit(ROOT.TFile.kRecovered),'f.IsZombie()',f.IsZombie()
                print 'File', del_protocol.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=',''), 'already exists but is buggy, gonna delete and rewrite it.'
                #command = 'rm %s' %(outputFile)
                command = 'srmrm %s' %(del_protocol)
                subprocess.call([command], shell=True)
                print(command)
            else: continue
        # print 'added to input'
        inputs.append((whereToLaunch,inputFile,outputFile,Acut,remove_branches))

    # print 'inputs',inputs
    outputs = []
    multiprocess=int(config.get('Configuration','nprocesses'))
    if multiprocess>1:
        ## process the input list (using multiprocess)
        from multiprocessing import Pool
        p = Pool(multiprocess)
        outputs = p.map(copySingleFileOneInput,inputs)
    else:
        for input_ in inputs:
                output = copySingleFileOneInput(input_)
                outputs.append(output)

    ## finally do the hadd of the copied trees
    if ('pisa' in whereToLaunch):
      fileToMerge = outputFile[:outputFile.rfind("tree_")+5]+"*"+outputFile[outputFile.rfind(".root"):]
      # command = "hadd -f "+pathOUT+'/'+newprefix+vhbbfolder+".root "+fileToMerge
      command = "hadd -f "+pathOUT+'/'+newprefix+folderName+".root "+fileToMerge
      print command
      os.system(command)

    print "##### COPY TREE - END ######"


def mergetreePSI(pathIN,pathOUT,prefix,newprefix,folderName,Aprefix,Acut,config):
    '''
    List of variables
    pathIN: path of the input file containing the data
    pathOUT: path of the output files
    prefix: "prefix" variable from "samples_nosplit.cfg"
    newprefix: "newprefix" variable from "samples_nosplit.cfg"
    file: sample header (as DYJetsToLL_M-50_TuneZ2Star_8TeV-madgraph-tarball)
    Aprefix: empty string ''
    Acut: the sample cut as defined in "samples_nosplit.cfg"
    '''
    print 'start mergetreePSI.py'
    print (pathIN,pathOUT,prefix,newprefix,folderName,Aprefix,Acut)
    print "##### MERGE TREE - BEGIN ######"

    merged = pathOUT+'/'+newprefix+folderName+".root "

    del_merged = merged
    del_merged = del_merged.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
    del_merged = del_merged.replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
    del_merged = del_merged.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
    command = 'srmrm %s' %(del_merged)
    print command
    subprocess.call([command], shell = True)
    t = ROOT.TFileMerger(ROOT.kFALSE)
    __tmpPath = os.environ["TMPDIR"]
    tmp_filename = __tmpPath+'/'+newprefix+folderName+".root "
    print 't.OutputFile('+tmp_filename+',"RECREATE")'
    t.OutputFile(tmp_filename, "RECREATE")
    outputFolder = "%s/%s/" %(pathOUT,folderName)
    print 'outputFolder is', outputFolder
    for file in os.listdir(outputFolder.replace('root://t3dcachedb03.psi.ch:1094','').replace('gsidcap://t3se01.psi.ch:22128/','').replace('dcap://t3se01.psi.ch:22125/','')):
        # print 'file is', outputFolder+file
        if file.startswith('tree'):
            print 't.AddFile('+outputFolder+file+')'
            t.AddFile(outputFolder+file)
    t.Merge()

    srmpathOUT = pathOUT.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
    srmpathOUT = srmpathOUT.replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
    srmpathOUT = srmpathOUT.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
    command = 'srmcp -2 -globus_tcp_port_range 20000,25000 file:///'+__tmpPath+'/'+newprefix+folderName+".root"+' '+srmpathOUT+'/'+newprefix+folderName+".root"
    print command
    subprocess.call([command], shell=True)

    print 'checking output file',pathOUT+'/'+newprefix+folderName+".root"
    f = ROOT.TFile.Open(pathOUT+'/'+newprefix+folderName+".root",'read')
    if not f or f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
        print 'TERREMOTO AND TRAGEDIA: THE MERGED FILE IS CORRUPTED!!! ERROR: exiting'
        sys.exit(1)

    command = 'rm '+__tmpPath+'/'+newprefix+folderName+'.root'
    print command
    subprocess.call([command], shell=True)

    print "##### MERGE TREE - END ######"

def filelist(pathIN,folderName):
    '''
    List of variables
    pathIN: path of the input file containing the data
    pathOUT: path of the output files
    prefix: "prefix" variable from "samples_nosplit.cfg"
    newprefix: "newprefix" variable from "samples_nosplit.cfg"
    file: sample header (as DYJetsToLL_M-50_TuneZ2Star_8TeV-madgraph-tarball)
    Aprefix: empty string ''
    Acut: the sample cut as defined in "samples_nosplit.cfg"
    '''
    # print 'start filelist'
    # print (pathIN,folderName)
    filenames = open(pathIN+'/'+folderName+'.txt').readlines()
    # print 'len(filenames)',len(filenames),filenames[2]

    ## search the folder containing the input files
    inputFiles = []
    # print "##### COPY TREE - BEGIN ######"

    for filename_ in filenames:
        if '.root' in filename_ :
            inputFiles.append(filename_.rstrip('\n'))

    return inputFiles

