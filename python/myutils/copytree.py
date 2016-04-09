import ROOT,sys,os,subprocess,random,string
from printcolor import printc

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def copySingleFile(whereToLaunch,inputFile,outputFile,Acut,remove_branches):
        print 'inputFile',inputFile
        if ('pisa' in whereToLaunch):
          input = ROOT.TFile.Open(inputFile,'read')
        else:
          input = ROOT.TFile.Open('root://t3dcachedb03.psi.ch:1094/'+inputFile,'read')

        output = ROOT.TFile.Open(outputFile,'create')
        print "Writing file:",outputFile

        input.ls()
        input.cd()
        obj = ROOT.TObject
        for key in ROOT.gDirectory.GetListOfKeys():
            input.cd()
            obj = key.ReadObj()
            #print obj.GetName()
            if obj.GetName() == 'tree':
                continue
            output.cd()
            #print key.GetName()
            obj.Write(key.GetName())

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
        output.ls()
        print "Writing output file"
        output.Write()
        print "Closing output file"
        output.Close()
        print "Closing input file"
        input.Close()

def copySingleFileOneInput(inputs):
    return copySingleFile(*inputs)

def copytree(pathIN,pathOUT,prefix,newprefix,folderName,Aprefix,Acut,config):
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
    print 'start copytree.py'
    print (pathIN,pathOUT,prefix,newprefix,folderName,Aprefix,Acut)

    ## search the folder containing the input files
    from os import walk
    dirpath = ""
    filename = ""
#    filenames = []
    inputFiles = []
    folder_prefix = ''
    print "##### COPY TREE - BEGIN ######"
    whereToLaunch = config.get('Configuration','whereToLaunch')
    remove_branches = config.get('General','remove_branches').replace("[","").replace("]","").replace("'","").split(',')
    print 'remove_branches:',remove_branches,'len(remove_branches):',len(remove_branches)

    if('pisa' in whereToLaunch):
      for (dirpath_, dirnames, filenames_) in walk(pathIN+'/'+folderName):
        for filename_ in filenames_:
            if 'root' in filename_ and not 'failed' in dirpath_:
                inputFiles.append(dirpath_+'/'+filename_)
    else:
      FOLDER = pathIN+'/'+folderName
      if FOLDER.startswith('dcap://t3se01.psi.ch:22125'):
          FOLDER = FOLDER.replace('dcap://t3se01.psi.ch:22125','')
          folder_prefix = 'dcap://t3se01.psi.ch:22125'
      for (dirpath_, dirnames, filenames_) in walk(FOLDER):
        for filename_ in filenames_:
            if 'root' in filename_ and not 'failed' in dirpath_:
                inputFiles.append(dirpath_+'/'+filename_)

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
          print 'checking and/or creating folder',_output_folder
          _output_folder += '/'+_folder
          if os.path.exists(_output_folder): print 'exists'
          else:
              print 'does not exist'
              command = 'srmmkdir srm://t3se01.psi.ch/' + _output_folder
              subprocess.call([command], shell = True)
          if os.path.exists(_output_folder): print 'Folder', _output_folder, 'sucessfully created'

    ## prepare a list of input(inputFile,outputFile,Acut) for the files to be processed
    inputs=[]
    filenames=[]
    for inputFile in inputFiles:
        subfolder = inputFile.split('/')[-4]
        filename = inputFile.split('/')[-1]
        filename = filename.split('_')[0]+'_'+subfolder+'_'+filename.split('_')[1]
        if filename in filenames: continue
        filenames.append(filename)
#        outputFile = "%s/%s/%s" %(pathOUT,folderName,filename.replace('.root','')+'_'+id_generator()+'.root')
        outputFile = "%s/%s/%s" %(pathOUT,folderName,filename.replace('.root','')+'.root')
        # print 'inputFile',inputFile,'outputFile',outputFile
        if('PSI' in whereToLaunch):
          del_protocol = outputFile
        else:
          del_protocol = pathOUT
          
        del_protocol = del_protocol.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
        del_protocol = del_protocol.replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
        del_protocol = del_protocol.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
        print "cutting ",inputFile," ---> ",outputFile
        
        if ('pisa' in whereToLaunch) and os.path.isfile(outputFile):
            command = 'rm %s' %(outputFile)
            print(command)
            subprocess.call([command], shell=True)
        elif('PSI' in whereToLaunch):
          if os.path.isfile(del_protocol.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=','')): 
            print 'File', del_protocol.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=',''), 'already exists.\n Gonna delete it.'
            #command = 'rm %s' %(outputFile)
            command = 'srmrm %s' %(del_protocol)
            print(command)
            subprocess.call([command], shell=True)
          else: print 'FALSE'
        inputs.append((whereToLaunch,inputFile,outputFile,Acut,remove_branches))

    ## process the input list (using multiprocess)
    multiprocess=int(config.get('Configuration','nprocesses'))
    outputs = []
    if multiprocess>1:
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

    else:
      merged = pathOUT+'/'+newprefix+folderName+".root "

      del_merged = merged
      del_merged = del_merged.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
      del_merged = del_merged.replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
      del_merged = del_merged.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
      command = 'srmrm %s' %(del_merged)
      print command
      subprocess.call([command], shell = True)
      #else: print 'Does not exist'
      t = ROOT.TFileMerger(ROOT.kFalse)
      t.OutputFile(pathOUT+'/'+newprefix+folderName+".root ", "CREATE")
      print 'outputFolder is', outputFolder 
      for file in os.listdir(outputFolder.replace('root://t3dcachedb03.psi.ch:1094','').replace('gsidcap://t3se01.psi.ch:22128/','').replace('dcap://t3se01.psi.ch:22125/','')):
          print 'file is', outputFolder+file
          if file.startswith('tree'):
              t.AddFile(outputFolder+file)
      t.Merge()
    
      print 'checking output file',pathOUT+'/'+newprefix+folderName+".root"
      f = ROOT.TFile.Open(pathOUT+'/'+newprefix+folderName+".root",'read')
      if f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
        print 'TERREMOTO AND TRAGEDIA: THE MERGED FILE IS CORRUPTED!!! ERROR: deleting it and exiting'
        subprocess.call([command], shell = True)
        sys.exit(1)
      else:
        for file in os.listdir(outputFolder.replace('root://t3dcachedb03.psi.ch:1094','').replace('gsidcap://t3se01.psi.ch:22128/','').replace('dcap://t3se01.psi.ch:22125/','')):
          filename = outputFolder+file
          filename = filename.replace('root://t3dcachedb03.psi.ch:1094','').replace('gsidcap://t3se01.psi.ch:22128/','').replace('dcap://t3se01.psi.ch:22125/','')
          print("srmrm srm://t3se01.psi.ch:8443/srm/managerv2?SFN="+filename)
          os.system("srmrm srm://t3se01.psi.ch:8443/srm/managerv2?SFN="+filename)

    print "##### COPY TREE - END ######"
