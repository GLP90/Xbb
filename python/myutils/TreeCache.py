from __future__ import print_function
import os,sys,subprocess,hashlib
import ROOT
from samplesclass import Sample
import time
import glob
import math
#from myutils.copytreePSI import filelist as getSampleFileList  # to avoid name conflict with filelist variable
from copytreePSI import filelist as getSampleFileList  # to avoid name conflict with filelist variable

class TreeCache:
    def __init__(self, cutList, sampleList, path, config,filelist=None,mergeplot=False,sample_to_merge=None,mergeCachingPart=-1,plotMergeCached=False, branch_to_keep=None, do_onlypart_n= False, dccut = None, remove_sys=None):
        ROOT.gROOT.SetBatch(True)
        self.verbose = False
        self.path = path
        self.config = config
        self.remove_sys = remove_sys
        self.do_onlypart_n = do_onlypart_n
        print("Init path",path)#," sampleList",sampleList)
        self._cutList = []
        self.dccut = None
        self.branch_to_keep = branch_to_keep
        if dccut:
            self.dccut = dccut
        #! Make the cut lists from inputs
        for cut in cutList:
            self._cutList.append('(%s)'%cut.replace(' ',''))
        try:
            self.__tmpPath = os.environ["TMPDIR"]
            print('The TMPDIR is ', os.environ["TMPDIR"])
            
        except KeyError:
            print("\x1b[32;5m %s \x1b[0m" %open('%s/data/vhbb.txt' %config.get('Directories','vhbbpath')).read())
            print("\x1b[31;5;1m\n\t>>> %s: Please set your TMPDIR and try again... <<<\n\x1b[0m" %os.getlogin())
            sys.exit(-1)

        if filelist:
            print('len(filelist)',len(filelist))

        self.__doCache = True
        if config.has_option('Directories','tmpSamples'):
            self.__cachedPath = config.get('Directories','tmpSamples')
        self.__hashDict = {}
        self.minCut = None
        self.__find_min_cut()# store the cut list as one string in minCut, using ROOT syntax (i.e. || to separate between each cut) 
        self.__sampleList = sampleList
        self.sample_to_merge = sample_to_merge

        # number of the chunk that should be processed
        self.mergeCachingPart = mergeCachingPart

        # use all the chunks of partially merged samples to plot (from mergecaching step)
        self.plotMergeCached =  plotMergeCached


        if self.plotMergeCached:
            print('\n\t>>> MERGE & PLOT <<<\n')
            self.__merge_cache_samples(filelist, self.mergeCachingPart)
        elif self.mergeCachingPart > -1:
            print('\n\t>>> Caching FILES, part ' + str(self.mergeCachingPart) +' <<<\n')
            self.__merge_cache_samples(filelist, self.mergeCachingPart)
        else:
            print('\n\t>>> Caching FILES <<<\n')
            self.__cache_samples(filelist,mergeplot)

    def putOptions(self):
        return (self.__sampleList,self.__doCache,self.__tmpPath,self._cutList,self.__hashDict,self.minCut,self.path)
    
    def _mkdir_recursive(self, path):
        sub_path = os.path.dirname(path)
        if not os.path.exists(sub_path):
            self._mkdir_recursive(sub_path)
        if not os.path.exists(path):
            os.mkdir(path)

    def __find_min_cut(self):
        effective_cuts = []
        #for dc step
        if self.dccut:
            self.minCut = '('+self.dccut+')'
        else:
            #remove repetition and (1) (the latter would keep all the events)
            for cut in self._cutList:
                if not cut in effective_cuts and not cut == "(1)":
                    effective_cuts.append(cut)
            self._cutList = effective_cuts
            self.minCut = '||'.join(self._cutList)

        #if self.dccut:
        #    self.minCut = '('+self.dccut+')&&('+self.minCut+')'


    def _subtrim_tree(self, input_hash, output_hash, theCut):
        '''Performs a finer caching from an already cached files, using as additional cuts the one used in the get_tree function'''

        print("==================")
        print("Perform subcaching")
        print("==================\n")

        print('Reading input', '%s/tmp_%s.root'%(self.__cachedPath,input_hash))
        input = ROOT.TFile.Open('%s/tmp_%s.root'%(self.__cachedPath,input_hash),'read')

        #if exist in tmpdir, just copy
        tmpfile = "%s/%s" %(self.__tmpPath,'tmp_'+str(output_hash)+'.root')
        outputFile = '%s/tmp_%s_%i.root'%(self.__cachedPath,output_hash,int(input_hash.split('_')[-1]))
        print('outputFile is', outputFile)

        if self.__doCache and self.file_exists(tmpfile):
            print ('File exists in TMPDIR, proceeding to the copy')
            command = 'xrdcp -d 1 '+tmpfile+' '+ outputFile
            print('the command is', command)
            subprocess.call([command], shell=True)
            return output_hash

        output = ROOT.TFile.Open(tmpfile,'recreate')

        #Skim input file
        print('The input file is', '%s/tmp_%s.root'%(self.__cachedPath,input_hash))
        input = ROOT.TFile.Open('%s/tmp_%s.root'%(self.__cachedPath,input_hash),'read')

        input.Print()
        print ("I read the tree")
        tree = input.Get("tree")
        assert type(tree) is ROOT.TTree

        input.cd()
        obj = ROOT.TObject
        for key in ROOT.gDirectory.GetListOfKeys():
            input.cd()
            obj = key.ReadObj()
            if obj.GetName() == 'tree':
                continue
            output.cd()
            obj.Write(key.GetName())
        output.cd()
        print ("(subtrimtree) the cut is", theCut)
        #Problem here: not working when empty tree

        cuttedTree=tree.CopyTree(theCut)
        cuttedTree.Write()
        output.Write()
        input.Close()
        del input
        output.Close()
        del output
        print ("Copying file to the tmp folder.")
        print('outputFile',outputFile)
        command = 'xrdcp -d 1 '+tmpfile+' '+ outputFile
        subprocess.call([command], shell=True)
        if '/scratch/' in  tmpfile: command = 'rm %s' %(tmpfile)
        else: command = 'gfal-rm %s' %(tmpfile)

    def _trim_tree(self, sample, filelist, mergeplot = False, forceReDo = False, mergeCachingPart = -1):

        start_time = time.time()
        print("Caching the sample")
        print("==================\n")

        ''' Create temporary file for each sample '''
        theName = sample.name
        print('Reading sample <<<< %s' %sample)
        # print('path',self.path,'get_path',sample.get_path)
        # print('filelist',filelist)
        inputfiles = []
        outputfiles = []
        tmpfiles = []
        # prefix
        tmpCache = ''
        tmpSource = ''
        theHash = ''

        if (not filelist or len(filelist) == 0) and self.plotMergeCached:
            print ('--> this is the Plotting step')
        elif not filelist or len(filelist) == 0 or mergeplot:
            source = '%s/%s' %(self.path,sample.get_path)
            inputfiles.append(source)
            checksum = self.get_checksum(source)
            #Important: new theHash only to reproduce 2016 dc.
            #theHash = hashlib.sha224('%s_s%s_%s' %(sample,checksum,self.minCut)).hexdigest()
            theHash = hashlib.sha224('%s_%s_split%d' %(sample,self.minCut,sample.mergeCachingSize)).hexdigest()
            self.__hashDict[theName] = theHash
            tmpSource = '%s/tmp_%s.root'%(self.__tmpPath,theHash)
            print('opening '+source)
            tmpfiles.append(tmpSource)
            tmpCache = '%s/tmp_%s.root'%(self.__cachedPath,theHash)
            outputfiles.append(tmpCache)
            print('tmpSource is', tmpSource)
            print('tmpCache is', tmpCache)
            print('MERGEPLOT IS',mergeplot)
            if eval(str(mergeplot)):
                 # mergetreePSI(pathIN, pathOUT,           prefix,  newprefix, folderName,        Aprefix, Acut, config):
                from mergetreePSI import mergetreePSI_def
                mergetreePSI_def(self.path, self.__cachedPath, theHash, "tmp_",    sample.identifier, hashlib.sha224(self.minCut).hexdigest(),      "",   "")
                return 0
        elif filelist and mergeCachingPart > -1:
            # merge caching uses unmerged input files and partially merges them in chunks up to sample.mergeCachingSize files

            # include sample(subsample name), cut(without subsample cut) and chunk size into the hash
            # changing the chunk size makes re-caching necessary
            hashString = '%s_%s_split%d' %(sample,self.minCut,sample.mergeCachingSize)
            theHash = hashlib.sha224(hashString).hexdigest()
            self.__hashDict[theName] = theHash
            print ('the hash string is: %s -> %s'%(hashString, theHash))

            # check for existence of the individual tree files
            filelistCopied = []
            for inputFile in filelist:
                print ('inputFile is', inputFile)
                try:
                    subfolder = inputFile.split('/')[-4]
                    filename = inputFile.split('/')[-1]
                    filename = filename.split('_')[0]+'_'+subfolder+'_'+filename.split('_')[1]
                    hash = hashlib.sha224(filename).hexdigest()
                    inputFileNew = "%s/%s/%s" %(self.path,sample.identifier,filename.replace('.root','')+'_'+str(hash)+'.root')
                    if self.verbose:
                        print('inputFile2',inputFileNew,'isfile',os.path.isfile(inputFileNew.replace('root://t3dcachedb03.psi.ch:1094/','')))
                    filelistCopied.append(inputFileNew)
                except Exception as e:
                    print ('Exception:'+str(e))
                    print ('ERROR occured for "'+inputFile+'"')
                    print ('->'+inputFileNew)

            # append semicolon separated list as single element to inputfiles list and just one file to tmpfiles
            inputfiles.append(';'.join(filelistCopied))
            tmpfile = '%s/tmp_%s_%d.root'%(self.__tmpPath,theHash,mergeCachingPart)
            tmpfiles.append(tmpfile)
            outputfile = '%s/tmp_%s_%d.root'%(self.__cachedPath,theHash,mergeCachingPart)
            outputfiles.append(outputfile)
            print (' input: %d files like %s\n tmp: %s\n output: %s'%(len(filelist), filelist[0], tmpfile, outputfile))

        else:
            outputFolder = "%s/%s" %(self.__cachedPath.replace('root://t3dcachedb03.psi.ch:1094/',''),sample.identifier)
            print('outputFolder is', outputFolder)
            if not os.path.isfile(outputFolder):
                createFolder = 'gfal-mkdir -p gsiftp://t3se01.psi.ch/' + outputFolder
                print('Will create the missing fodler using the command', createFolder)
                subprocess.call([createFolder], shell=True)# delete the files a
            for inputFile in filelist:
                # print('inputFile',inputFile)
                subfolder = inputFile.split('/')[-4]
                # print('subfolder',subfolder)
                filename = inputFile.split('/')[-1]
                # print('filename1',filename)
                filename = filename.split('_')[0]+'_'+subfolder+'_'+filename.split('_')[1]
                # print('filename2',filename)
                hash = hashlib.sha224(filename).hexdigest()
                inputFile = "%s/%s/%s" %(self.path,sample.identifier,filename.replace('.root','')+'_'+str(hash)+'.root')
                isFile = os.path.isfile(inputFile.replace('root://t3dcachedb03.psi.ch:1094/',''))
                if not sFile:
                    print ('file ',inputFile, ' does not exist => skip!')
                    continue
                hash = hashlib.sha224(self.minCut).hexdigest()
                outputFile = "%s/%s/%s" %(self.__cachedPath,sample.identifier,filename.replace('.root','')+'_'+str(hash)+'.root')
                print('outputFile',outputFile)
                tmpfile = "%s/%s" %(self.__tmpPath,filename.replace('.root','')+'_'+str(hash)+'.root')
                print('tmpfile',tmpfile)
                if inputFile in inputfiles: continue
                del_protocol = outputFile
                del_protocol = del_protocol.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                del_protocol = del_protocol.replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                del_protocol = del_protocol.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                if os.path.isfile(del_protocol.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=','')):
                    f = ROOT.TFile.Open(outputFile,'read')
                    if not f:
                      print('file is null, adding to input')
                      inputfiles.append(inputFile)
                      outputfiles.append(outputFile)
                      tmpfiles.append(tmpfile)
                      continue
                    # f.Print()
                    if f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
                        print('f.GetNkeys()',f.GetNkeys(),'f.TestBit(ROOT.TFile.kRecovered)',f.TestBit(ROOT.TFile.kRecovered),'f.IsZombie()',f.IsZombie())
                        print('File', del_protocol.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=',''), 'already exists but is buggy, gonna delete and rewrite it.')
                        #command = 'srmrm %s' %(del_protocol)
                        subprocess.call([command], shell=True)
                        print(command)
                        # todo: WTF is happening above, what is in command when this is commented out ????
                    else: continue
                inputfiles.append(inputFile)
                outputfiles.append(outputFile)
                tmpfiles.append(tmpfile)
        print('inputfiles',inputfiles,'tmpfiles',tmpfiles)

        ######################################################################
        # todo: add files to list of list instead of separate lists and zipping
        for inputfile,tmpfile,outputFile in zip(inputfiles,tmpfiles,outputfiles):

            #print('the tmp source is ', tmpSource)
            #print ('self.__doCache',self.__doCache,'self.file_exists(tmpSource)',self.file_exists(tmpSource))
            print("==================================================================")
            print ('The cut is ', self.minCut)
            print("==================================================================\n")

            #------------------------------------------------------------------------------------------------------------
            # check if CACHED file is existing
            #------------------------------------------------------------------------------------------------------------
            if self.__doCache and self.file_exists(outputFile) and not forceReDo and ((not filelist or len(filelist) == 0) or mergeCachingPart > -1):
                print('sample',theName,'skipped, filename=',outputFile)
                return (theName,theHash)
            else:
                # -------------------------------------------------------------------------------------------------------
                #  check if TMP file is existing: yes -> copy to CACHED
                # -------------------------------------------------------------------------------------------------------
                if self.__doCache and self.file_exists(tmpfile) and not forceReDo:
                    print ('File exists in TMPDIR, proceeding to the copy')
                    print ('sample',theName,'skipped, filename=',tmpfile)

                    # check if file contains data and is not flagged broken
                    f = ROOT.TFile.Open(tmpfile,'read')
                    if not f or f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
                        print ('File is null. Gonna redo it.')
                        del_protocol = file.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                        if '/scratch/' in  del_protocol: command = 'rm %s' %(del_protocol)
                        else: command = 'gfal-rm %s' %(del_protocol)
                        subprocess.call([command], shell=True)
                        print(command)
                    else:
                        f.Close()
                        command = 'xrdcp -d 1 '+tmpfile+' '+ outputFile
                        print('the command is', command)
                        returnCode = subprocess.call([command], shell=True)
                        if returnCode != 0:
                            print ('\x1b[31mERROR: XRDCP failed for {tmpfile}->{outputfile} !\x1b[0m'.format(tmpfile=tmpfile, outputfile=outputFile))
                        if len(filelist) == 0: return (theName,theHash)

            print ('trying to create',tmpfile)
            print ('self.__tmpPath',self.__tmpPath)

            # todo: below...
            if self.__tmpPath.find('root://t3dcachedb03.psi.ch:1094/') != -1:
                mkdir_command = self.__tmpPath.replace('root://t3dcachedb03.psi.ch:1094/','')
                print('mkdir_command',mkdir_command)
                # RECURSIVELY CREATE REMOTE FOLDER ON PSI SE, but only up to 3 new levels
                mkdir_command1 = mkdir_command.rsplit('/',1)[0]
                mkdir_command2 = mkdir_command1.rsplit('/',1)[0]
                mkdir_command3 = mkdir_command2.rsplit('/',1)[0]
                my_user = os.popen("whoami").read().strip('\n').strip('\r')+'/'
                if my_user in mkdir_command3:
                  print ('mkdir_command3',mkdir_command3)
                  subprocess.call(["uberftp t3se01 'mkdir "+mkdir_command3+" ' "], shell=True)# delete the files already created ?
                  " "
                if my_user in mkdir_command2:
                  print ('mkdir_command2',mkdir_command2)
                  subprocess.call(["uberftp t3se01 'mkdir "+mkdir_command2+" ' "], shell=True)# delete the files already created ?
                if my_user in mkdir_command1:
                  print ('mkdir_command1',mkdir_command1)
                  subprocess.call(["uberftp t3se01 'mkdir "+mkdir_command1+" ' "], shell=True)# delete the files already created ?
                if my_user in mkdir_command:
                  print ('mkdir_command',mkdir_command)
                  subprocess.call(["uberftp t3se01 'mkdir "+mkdir_command+" ' "], shell=True)# delete the files already created ?
            else:
                mkdir_command = self.__tmpPath
                print('mkdir_command',mkdir_command)
                # RECURSIVELY CREATE REMOTE FOLDER ON PSI SE, but only up to 3 new levels
                mkdir_command1 = mkdir_command.rsplit('/',1)[0]
                mkdir_command2 = mkdir_command1.rsplit('/',1)[0]
                mkdir_command3 = mkdir_command2.rsplit('/',1)[0]
                my_user = os.popen("whoami").read().strip('\n').strip('\r')+'/'
                if my_user in mkdir_command and not os.path.exists(mkdir_command):
                  print ('mkdir_command',mkdir_command)
                  subprocess.call(['mkdir '+mkdir_command], shell=True)# delete the files already created ?

            try:
                print("Writing: ",tmpfile)
                #! read the tree from the input
                if forceReDo:
                    output = ROOT.TFile.Open(tmpfile,'recreate')
                else:
                    output = ROOT.TFile.Open(tmpfile,'create')
                output.cd()
            except:
                ## in case there are problems go to the next dataset [probably another process is working on this dataset]
                if len(filelist) == 0: return (theName,theHash)
                else: print('PROBLEM WITH FILE!!',tmpfile); continue
            if ';' in inputfile:
                print ('reading inputfiles...')
            else:
                print ('reading inputfile',inputfile)

            treeEmpty = True
            # ----------------------------------------------------------------------------------------------------------
            #  READ INPUT files
            # ----------------------------------------------------------------------------------------------------------
            # list -> TChain
            if ';' in inputfile:
                tree = ROOT.TChain(sample.tree)
                histograms = {}
                time1=time.time()
                nFilesChained = 0
                for rootFileName in inputfile.split(';'):
                    chainTree = '%s/%s'%(rootFileName, sample.tree)
                    if os.path.isfile(rootFileName.replace('root://t3dcachedb03.psi.ch:1094/','')):
                        obj = None
                        input = ROOT.TFile.Open(rootFileName,'read')
                        if input and not input.IsZombie():

                            # add count histograms, since there are not in the tchain
                            for key in input.GetListOfKeys():
                                obj = key.ReadObj()
                                if obj.GetName() == 'tree':
                                    continue
                                if obj.GetName() in histograms:
                                    if histograms[obj.GetName()]:
                                        histograms[obj.GetName()].Add(obj.Clone(obj.GetName()))
                                    else:
                                        print ("ERROR: histogram object was None!!!")
                                else:
                                    histograms[obj.GetName()] = obj.Clone(obj.GetName())
                                    histograms[obj.GetName()].SetDirectory(output)
                            input.Close()

                            # add file to chain
                            if self.verbose:
                                print ('chaining '+chainTree)
                            statusCode = tree.Add(chainTree)
                            if statusCode != 1 or not tree:
                                print ('ERROR: failed to chain ' + chainTree + ', returned: ' + str(statusCode),'tree:',tree)
                                raise Exception("TChain method Add failure")
                            else:
                                treeEmpty = False
                                nFilesChained += 1
                        else:
                            print ('ERROR: Cant open file:'+chainTree)
                assert type(tree) is ROOT.TChain
                time2=time.time()
                print ('adding %d files to chain took %f seconds.'%(nFilesChained, time2-time1))
                input = None
                if self.verbose:
                    print ("HISTOGRAMS: %r"%histograms)
                output.cd()
                for histogramName, histogram in histograms.iteritems():
                    histogram.SetDirectory(output)

            # single input file -> read it as TFile
            else:
                print ("I am reading")
                input = ROOT.TFile.Open(inputfile,'read')
                input.Print()
                print ("I read the tree")
                tree = input.Get(sample.tree)
                assert type(tree) is ROOT.TTree
                treeEmpty = False
                input.cd()

                obj = ROOT.TObject
                for key in ROOT.gDirectory.GetListOfKeys():
                    input.cd()
                    obj = key.ReadObj()
                    if obj.GetName() == 'tree':
                        continue
                    output.cd()
                    obj.Write(key.GetName())

            # ----------------------------------------------------------------------------------------------------------
            #  CUTS
            # ----------------------------------------------------------------------------------------------------------
            output.cd()
            theCut = self.minCut
            #if sample.subsample:
            #    theCut = '((%s)&(%s))' %(theCut,sample.subcut)
            #print ("the cut (with subcut) is", theCut)

            if not treeEmpty:
                time1 = time.time()

                subcutExists = sample.subcut and sample.subcut.strip() != "1"

                # remove branches from tree
                if self.remove_sys:
                    tree.SetBranchStatus("*Down",0)
                    tree.SetBranchStatus("*Up",0)
                    
                removeBranches = []
                remove_useless_branch = False
                remove_useless_after_sys = False

                try:
                   remove_useless_branch = self.config.get('Analysis', 'remove_useless_branch').lower().strip() == 'true'
                except:
                   remove_useless_branch = False

                try:
                   remove_useless_after_sys = self.config.get('Analysis', 'remove_useless_after_sys').lower().strip() == 'true'
                except:
                   remove_useless_after_sys = False

                if remove_useless_branch:
                    try:
                        removeBranches += eval(self.config.get('Branches','useless_after_sys'))
                    except:
                        pass
                if remove_useless_after_sys:
                    try:
                        removeBranches += eval(self.config.get('Branches','useless_branch'))
                    except:
                        pass

                for branch in removeBranches:
                    try:
                        #print ('will remove', branch)
                        tree.SetBranchStatus(branch,0)
                    except:
                        pass
                if self.branch_to_keep:
                    tree.SetBranchStatus('*',0)
                    for b in self.branch_to_keep:
                        tree.SetBranchStatus(b,1)


                #time2 = time.time()
                #print ('DEBUG: tree=',tree)
                #totalCut = '(%s)&(%s)'%(theCut, sample.subcut) if subcutExists else theCut
                #cutTree = tree.CopyTree(totalCut, "")
                #time3 = time.time()
                #print ('cut done in ' + str(time3-time2) + ' s')
               
                #str_limit = 3000.
                if not self.dccut:
                #if len(theCut) < str_limit:

                    time2 = time.time()
                    print ('normal caching')
                    print ('DEBUG: tree=',tree)
                    print ('theCut is', theCut)
                    cutFormula = ROOT.TTreeFormula("cutFormula", theCut, tree)
                    subcutFormula = ROOT.TTreeFormula("subcutFormula", sample.subcut if subcutExists else '1', tree)

                    cutTree = tree.CloneTree(0)
                    print ('lolol')
                    i = 0
                    s = 0
                    s2 = 0
                    print (theCut)
                    print (sample.subcut)
                    oldTreeNum = -1
                    totalEntries = 0
                    finalEntries = 0
                    for event in tree:
                        tree.LoadTree(i)
                        treeNum = tree.GetTreeNumber()
                        if treeNum != oldTreeNum:
                            cutFormula.UpdateFormulaLeaves()
                            subcutFormula.UpdateFormulaLeaves()
                            oldTreeNum = treeNum

                        # the GetNdata() here is used because of its side-effects!
                        n1 = cutFormula.GetNdata()
                        s = cutFormula.EvalInstance()
                        if s:
                            n2 = subcutFormula.GetNdata()
                            s2 = subcutFormula.EvalInstance()
                            if s and s2:
                               cutTree.Fill()
                               finalEntries += 1
                        totalEntries += 1
                        i += 1
                else:
                    #cutformula_list =[]
                    #for formula_cut in self._cutList:
                    #    if formula_cut == "(1)": continue
                    #    formula = ROOT.TTreeFormula("cutFormula%i"%self._cutList.index(formula_cut), formula_cut, tree)
                    #    cutformula_list.append(formula)

                    print ('cut_list is', self._cutList)

                    #loop over the tree and apply cut
                    time2 = time.time()
                    print ('caching for dc')
                    print ('DEBUG: tree=',tree)
                    print ('dccut is', self.dccut)
                    subcutFormula = ROOT.TTreeFormula("subcutFormula", sample.subcut if subcutExists else '1', tree)
                    dccutFormula = ROOT.TTreeFormula("dccut", self.dccut, tree)

                    cutTree = tree.CloneTree(0)
                    print ('lolol')
                    i = 0
                    print (theCut)
                    print (sample.subcut)
                    oldTreeNum = -1
                    totalEntries = 0
                    finalEntries = 0
                    for event in tree:

                        s1 = -1
                        s2 = -1
                        #s3 = -1

                        tree.LoadTree(i)
                        treeNum = tree.GetTreeNumber()

                        if treeNum != oldTreeNum:
                            dccutFormula.UpdateFormulaLeaves()
                            subcutFormula.UpdateFormulaLeaves()
                            #for formula in cutformula_list:
                            #    formula.UpdateFormulaLeaves()
                            oldTreeNum = treeNum

                        pass_cut = False

                        #if treeNum != oldTreeNum:
                        #    dccutFormula.UpdateFormulaLeaves()

                        n1 = dccutFormula.GetNdata()
                        s1 = dccutFormula.EvalInstance()

                        if s1 == 1.0:
                            n2 = subcutFormula.GetNdata()
                            s2 = subcutFormula.EvalInstance()
                            if s2 == 1.0:
                                pass_cut = True
                                #for formula in cutformula_list:
                                #    n3 = formula.GetNdata()
                                #    s3 = formula.EvalInstance()
                                #    if s3 == 1.0:
                                #        pass_cut = True
                                #        break
                        #print ('s1, s2, s3 are', s1, s2, s3)
                        if pass_cut:
                            cutTree.Fill()
                            finalEntries += 1

                        totalEntries += 1
                        i += 1
                
                time3 = time.time()
                print ('cut done in ' + str(time3-time2) + ' s' + ' ' + str(finalEntries) + '/' + str(totalEntries))
                
                ## first cut, without subcut
                #if subcutExists:
                #    gROOT->cd()
                #cuttedTree=tree.CopyTree(theCut,"")
                #print ('cut done: '+str(cuttedTree)+' '+str(tree.GetEntries()) + ' => ' + str(cuttedTree.GetEntries()) + ' entries')
                #time2=time.time()

                ## if subcut exists, apply it by further cutting the tree
                #if subcutExists:
                #    theSubcut = ('(%s)'%sample.subcut).replace(' ','')
                #    print ('the subcut is: '+theSubcut)
                #    output.cd()
                #    print ('scan done')
                #    #cuttedTree.SetDebug(1)
                #    #tree.SetDebug(1)
                #    subcutTree=cuttedTree.CopyTree(theSubcut)
                #    time3 = time.time()
                #    print ('subcutting done: '+str(subcutTree))
                #    subcutTree.SetDirectory(output)
                #else:
                #    time3 = time.time()
                #    cuttedTree.SetDirectory(output)
                #time4 = time.time()
                #print ('Cut1:'+str(time2-time1)+' Cut2:'+str(time3-time2)+' more:'+str(time4-time3))

            # ----------------------------------------------------------------------------------------------------------
            #  write OUTPUT
            # ----------------------------------------------------------------------------------------------------------
            print ('write to file')
            if output:
                output.Write()
                print ('file witten')
            if input:
                input.Close()
                #del input
            output.Close()
    #        tmpSourceFile = ROOT.TFile.Open(tmpSource,'read')
    #        if tmpSourceFile.IsZombie():
    #            print("@ERROR: Zombie file")
            #del output
            print ("debug4")
            print ("I've done " + theName + " in " + str(time.time() - start_time) + " s.")
            print ("Copying file to the tmp folder.")
            print('outputFile',outputFile)
            command = 'xrdcp -d 1 '+tmpfile+' '+ outputFile
            print('the command is', command)
            subprocess.call([command], shell=True)
            if '/scratch/' in  tmpfile: command = 'rm %s' %(tmpfile)
            else: command = 'gfal-rm %s' %(tmpfile)
            if not filelist or len(filelist) == 0: return (theName,theHash)


    def __merge_cache_samples(self, filelist=None, mergeCachingPart=-1):
        print ('__merge_cache_samples')
        if self.sample_to_merge:
            print ('prepare to __merge_cache_samples: %s'%self.sample_to_merge)

            # check if supplied sample name corresponds to existing sample
            sampleDictionary = {}
            matchedSample = None
            for sample in self.__sampleList:

                # compare extension
                extMatch = ('_ext' in str(sample)) == ('_ext' in self.sample_to_merge)
                if extMatch and '_ext' in str(sample):

                    # compare ext number
                    extToMerge = self.sample_to_merge.split('_ext')[1].strip()
                    extCompare = str(sample).split('_ext')[1].strip()
                    extMatch = extMatch and (extToMerge==extCompare)

                    # compare ext number in files list
                    # for file in filelist:
                    #    extMatch = extMatch and sample.identifier[sample.identifier.find('_ext'):] in file

                    pureSampleName = str(sample).split('_ext')[0]
                    pureSampleLongName = sample.identifier.split('_ext')[0]
                    pureNameSampleToMerge = self.sample_to_merge.split('_ext')[0]
                else:
                    pureSampleName = str(sample)
                    pureSampleLongName = sample.identifier
                    pureNameSampleToMerge = self.sample_to_merge

                # compare name
                sampleMatch = pureNameSampleToMerge.strip() == pureSampleName.strip()

                # compare name in files list
                # -> does not work, not exactly the same names
                # for file in filelist:
                #    sampleMatch = sampleMatch and ('/%s/'%pureSampleLongName) in file

                if extMatch and sampleMatch:
                    matchedSample = sample
                    print ('matching sample found:'+str(matchedSample))
                    break

            if matchedSample:
                self._trim_tree(sample=matchedSample, filelist=filelist, mergeplot=False, forceReDo=False, mergeCachingPart=mergeCachingPart)
            else:
                print ('not in list of samples!')
                for sample in self.__sampleList:
                    print ("--"+str(sample))
        else:
            # for plotting:
            #  get list of previously cached files and check if number of files matches expectations
            #stop if a file is missing
            file_missing = False
            for sample in self.__sampleList:
                theHash = hashlib.sha224('%s_%s_split%d' %(sample,self.minCut,sample.mergeCachingSize)).hexdigest()
                tmpFileMask = '{tmpdir}/tmp_{hash}_{part}.root'.format(tmpdir=self.__cachedPath, hash=theHash, part='*')
                tmpFileMask = tmpFileMask.replace('root://t3dcachedb03.psi.ch:1094','')

                # get list of unmerged root files
                samplefiles = self.config.get('Directories','samplefiles')
                unmergedFiles = getSampleFileList(samplefiles, sample.identifier)

                # merged and cached files
                mergedFiles = glob.glob(tmpFileMask)

                # get list of files which should exist
                mergeList = [unmergedFiles[x:x+sample.mergeCachingSize] for x in xrange(0, len(unmergedFiles), sample.mergeCachingSize)]

                # compare filenames from cached files with expectation from mergeList
                print ('%s (%s): %d/%d'%(sample.FullName, tmpFileMask.split('/')[-1], len(mergedFiles), len(mergeList)))

                for i,mergeListPart in enumerate(mergeList):
                    found = False
                    for mergedFile in mergedFiles:
                        if mergedFile.endswith('_%d.root'%i):
                            found = True
                            break
                    if not found:
                        print ('  \x1b[31mmissing:','part ',i,':','(hash)_%d.root'%i,'\x1b[0m')
                        if not self.do_onlypart_n:
                            file_missing = True
                            #raise Exception('files missing')
                if (len(mergeList) != len(mergedFiles)):
                    print ('\x1b[31mERROR len(mergeList) != len(mergedFiles) \x1b[0m')
                    #Need to continue for the training in order to run in parallel
                    if not self.do_onlypart_n:
                        file_missing = True
                        #raise Exception('files missing')

                # extract hashes from filenames and pass them as a list to __hashDict
                self.__hashDict[sample.name] = [x.split('/')[-1].replace('tmp_','').split('.')[0] for x in mergedFiles]
            if file_missing:
                raise Exception('files missing')
            #print( "DICT:",self.__hashDict)

    def __cache_samples(self,filelist=None,mergeplot=False):
        inputs=[]
        skip = True 
        # todo: this is not a job, but a sample...
        for job in self.__sampleList:
            # test1 = [method for method in dir(job) if callable(getattr(job, method))]
            # print(test1)
            # print(dir(job))
            # print('__doc__',job.__doc__,'\n__eq__',job.__eq__,'\n__init__',job.__init__,'\n__module__',job.__module__,'\n__str__',job.__str__,'\nactive',job.active,'\naddtreecut',job.addtreecut,'\ncount',job.count,'\nget_path',job.get_path,'\ngroup',job.group,'\nidentifier',job.identifier,'\nlumi',job.lumi,'\nname',job.name,'\nprefix',job.prefix,'\nsf',job.sf,'\nspecialweight',job.specialweight,'\nsubcut',job.subcut,'\nsubsample',job.subsample,'\ntree',job.tree,'\ntreecut',job.treecut,'\ntype',job.type,'\nweightexpression',job.weightexpression,'\nxsec',job.xsec)
            # sys.exit()

            # print("__cache_samples(",filelist,",",mergeplot,")")
            if self.sample_to_merge and (str(job) != self.sample_to_merge):
                continue
            skip = False 
            samplematch = False
            if filelist and not mergeplot:
                if not 'Run' in job.identifier:
                    # print('no RUN','job.identifier',job.identifier,'filelist[0]',filelist[0])
                    #no ext case
                    if len(job.identifier.split('_ext')) == 1 and len(filelist[0].split('_ext')) == 1:
                        samplematch = '/'+job.identifier+'/' in filelist[0]
                    #ext case
                    else:
                        samplematch_noext = '/'+job.identifier.split('_ext')[0]+'/' in filelist[0]
                        samplematch = samplematch_noext and ('_ext'+job.identifier.split('_ext')[1] in filelist[0])
                else:
                    samplematch = '/'+job.identifier.split('__')[0]+'/' in filelist[0]

            elif filelist and mergeplot:
                if not 'Run' in job.identifier:
                    # print('no RUN','job.identifier',job.identifier,'filelist[0]',filelist[0])
                    #no ext case
                    if len(job.identifier.split('_ext')) == 1 and len(filelist[0].split('_ext')) == 1:
                        samplematch = job.identifier in filelist[0]
                    #ext case
                    elif len(job.identifier.split('_ext')) == 1 and len(filelist[0].split('_ext')) != 1:
                        pass
                    else:
                        samplematch_noext = job.identifier.split('_ext')[0] in filelist[0]
                        samplematch = samplematch_noext and ('_ext'+job.identifier.split('_ext')[1] in filelist[0])
                else:
                    samplematch = '/'+job.identifier.split('__')[0]+'/' in filelist[0]
            else:
                samplematch = True

            if samplematch: print('job.name',job.name,'samplematch',samplematch)#,'filelist',filelist)
            if samplematch:
                inputs.append((self,"_trim_tree",(job),(filelist),(mergeplot)))

        if skip:
            print('@INFO: no samples has been found')
            return 1
        multiprocess=0
        # if('pisa' in self.config.get('Configuration','whereToLaunch')):
        multiprocess=int(self.config.get('Configuration','nprocesses'))
        outputs = []
        print('launching __cache_samples with ',multiprocess,' processes')
        if multiprocess>1:
            from multiprocessing import Pool
            from myutils import GlobalFunction
            p = Pool(multiprocess)
            outputs = p.map(GlobalFunction, inputs)
        else:
            for input_ in inputs:
                #CACHING OF THE FILES HAPPENS HERE!!!!! THIS IS EQUIVALENT TO
                # self._trim_tree(job,filenames,mergeplot)
                outputs.append((getattr(input_[0],input_[1])(input_[2],input_[3],input_[4])))
        if not filelist or  len(filelist)==0:
        # for output in outputs:
            (theName,theHash) = outputs[0]
            self.__hashDict[theName]=theHash

    def get_tree(self, sample, cut):
        #print (self.__hashDict)
        inputHashes = self.__hashDict[sample.name]
        print('input file %s/tmp_\x1b[32m%r\x1b[0m.root'%(self.__cachedPath, inputHashes))
        #fill all Count* histos as lists, like self.CountWeighted = [123.23]
        inputHashesList = inputHashes if type(inputHashes) == list else [inputHashes]
        #print ('inputHashesList is', inputHashesList)
        for inputHash in inputHashesList:
            if self.do_onlypart_n and not (inputHash.endswith('_%i'%(self.mergeCachingPart) )):
                continue
            input = ROOT.TFile.Open('{tmpdir}/tmp_{hash}.root'.format(tmpdir=self.__cachedPath, hash=inputHash),'read')
            if not input.IsZombie():
                for obj in input.GetListOfKeys():
                    name = obj.GetName()
                    if "Count" in name:
                        obj = obj.ReadObj()
                        assert(type(obj) is ROOT.TH1F)
                        counts = []
                        for i in range(obj.GetNbinsX()):
                            value = obj.GetBinContent(i+1)
                            if value<=0:
                                print("WARNING: bin ",i+1," of ",name," is ",value,". I'm forcing it to be 1.")
                                value=1
                            counts.append(value)

                        # sum the counts from the Count* histograms for all parts
                        # todo: write that to a proper dictionary instead of using members and setattr...
                        prevValue = [0]*len(counts)
                        try:
                            prevValue = getattr(self,name)
                        except:
                            pass
                        setattr(self, name, [x+y for x,y in zip(prevValue, counts)])
            else:
                print ('ERROR: in reading count histograms, iszombie:'+rootFileName)
            input.Close()

        # read TTree as TChain if multiple files given
        if type(inputHashes) == list:
            #tree = ROOT.TChain('tree')
            #for inputHash in inputHashes:
            #    status = tree.Add('{tmpdir}/tmp_{hash}.root/{treename}'.format(tmpdir=self.__cachedPath, hash=inputHash, treename='tree'), 0)
            #    if status != 1:
            #        print ('ERROR: cannot add file to chain:'+inputHash+'=>'+str(status))
            input = None
        # else read normally as TFile
        else:
            rootFileName = '{tmpdir}/tmp_{hash}.root'.format(tmpdir=self.__cachedPath, hash=inputHashes)
            input = ROOT.TFile.Open(rootFileName,'read')
            print ('Opening %s'%rootFileName)
            tree = input.Get(sample.tree)

            # check if tree is existing
            try:
                assert (type(tree) is ROOT.TTree or type(tree) is ROOT.TChain)
            except:
                print ("%s/tmp_%s.root is corrupted. I'm relaunching _trim_tree"%(self.__cachedPath,self.__hashDict[sample.name]))
                self._trim_tree(sample, None, False,forceReDo=True)
                input = ROOT.TFile.Open('%s/tmp_%s.root'%(self.__cachedPath,self.__hashDict[sample.name]),'read')
                tree = input.Get(sample.tree)
                print("Type of sample.tree ROOT.TTree? (again) ", type(tree) is ROOT.TTree)

        print('cut is', cut)
        ROOT.gROOT.cd()
        print('getting the tree after applying cuts')
        if input:
            input.Close()
            del input
            del tree

        # if no additional cuts are applied, just return the already cached file
        if cut == '' or cut == '1':
            if type(inputHashes) == list:
                return ['%s/tmp_%s.root'%(self.__cachedPath, hash) for hash in self.__hashDict[sample.name]]
            else:
                return '%s/tmp_%s.root'%(self.__cachedPath,self.__hashDict[sample.name])
        # otherwise do the whole caching stuff again...
        else:
            inputHashesList = inputHashes if type(inputHashes) == list else [inputHashes]
            subcutFileNames = []
            for inputHash in inputHashesList:
                if self.do_onlypart_n and not (inputHash.endswith('_%i'%(self.mergeCachingPart) )):
                    continue
                subcut_hash = hashlib.sha224('%s_%s'%(inputHash,cut)).hexdigest()
                print('subcut input file %s/tmp_%s_%i.root'%(self.__cachedPath, subcut_hash,int(inputHash.split('_')[-1])))
                input_ = '%s/tmp_%s_%i.root'%(self.__cachedPath, subcut_hash,int(inputHash.split('_')[-1]))
                input = ROOT.TFile.Open(input_,'read')
                print('Opening ', input_)
                try:
                    tree = input.Get(sample.tree)
                    assert type(tree) is ROOT.TTree
                except:
                    print (input_,"is corrupted. I'm relaunching _subtrim_tree")
                    self._subtrim_tree(inputHash, subcut_hash, cut)
                    #input_ = '%s/tmp_%s.root'%(self.__cachedPath, subcut_hash)
                    input_ = '%s/tmp_%s_%i.root'%(self.__cachedPath, subcut_hash,int(inputHash.split('_')[-1]))
                    input = ROOT.TFile.Open(input_,'read')
                    if input.IsZombie():
                        print ('ERROR: file with subcuts is zombie:' + input_)
                    tree = input.Get(sample.tree)
                subcutFileNames.append('%s/tmp_%s_%i.root'%(self.__cachedPath, subcut_hash,int(inputHash.split('_')[-1])))

            if len(subcutFileNames) == 1:
                return subcutFileNames[0]
            else:
                return subcutFileNames



    #def get_copy_tree(self, sample, cut):
    #    input = ROOT.TFile.Open(self.get_tree(sample, cut),'read')
    #    tree = input.Get(sample.tree)
    #    cuttedTree=tree.CopyTree(cut)
    #    cuttedTree.SetDirectory(0)
    #    return cuttedTree


    @staticmethod
    def get_slc_version():
        command = 'uname -a'
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)
        lines = p.stdout.readlines()
        line = lines[0].split()[2]
        if 'el5' in line:
            return 'SLC5'
        elif 'el6' in line:
            return 'SLC6'
        else:
            sys.exit(-1)

    # @staticmethod
    #def get_scale(sample, config, lumi = None, count=1):
#   #     print float(sample.lumi)
    #    try: sample.xsec = sample.xsec[0]
    #    except: pass
    #    anaTag=config.get('Analysis','tag')
    #    theScale = 1.
    #    lumi = float(sample.lumi)
    #    print ('SCALE')
    #    print ('count is', count)
    #    theScale = lumi*sample.xsec*sample.sf/(count)
    #    print("sample: ",sample,"lumi: ",lumi,"xsec: ",sample.xsec,"sample.sf: ",sample.sf,"count: ",count," ---> using scale: ", theScale)
    #    return theScale

    def get_weight_histogram(self, inputHashes, histogramName):
        inputHashesList = inputHashes if type(inputHashes) == list else [inputHashes]
        weightHistogram = None
        for inputHash in inputHashesList:
            rootFileName = '%s/tmp_%s.root'%(self.__cachedPath, inputHash)
            rootFile = ROOT.TFile.Open(rootFileName,'read')

            if rootFile and not rootFile.IsZombie():
                if weightHistogram:
                    additionalWeightHistogram = rootFile.Get(histogramName)
                    if additionalWeightHistogram:
                        weightHistogram.Add(additionalWeightHistogram)
                    else:
                        print ('\x1b[31mERROR: did not find count histogram in {rootFileName} ({hash})\x1b[0m'.format(rootFileName=rootFileName, hash=inputHash))
                else:
                    fileHistogram = rootFile.Get(histogramName)
                    if fileHistogram:
                        weightHistogram = fileHistogram.Clone(histogramName)
                        weightHistogram.SetDirectory(0)
                    else:
                        print ('\x1b[31mERROR: did not find count histogram {histogram} in {file}\x1b[0m'.format(histogram=histogramName, file=rootFileName))

                rootFile.Close()
            else:
                print ('\x1b[31mERROR: zombie: {file}\x1b[0m'.format(file=rootFileName))
                del_protocol = rootFileName.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                if '/scratch/' in  del_protocol: command = 'rm %s' %(del_protocol)
                else: command = 'gfal-rm %s' %(del_protocol)
                subprocess.call([command], shell=True)
                print(command)
                raise Exception("root file with weight histogram is zombie. Deleting the file.")
        return weightHistogram

    def get_scale_training(self, sample, config, lumi = None, count=1):
        try: sample.xsec = sample.xsec[0]
        except: pass
        self.__cachedPath
        posWeight = self.get_weight_histogram(self.__hashDict[sample.name], 'CountPosWeight') #input.Get('CountPosWeight')
        negWeight = self.get_weight_histogram(self.__hashDict[sample.name], 'CountNegWeight') #input.Get('CountNegWeight')
        anaTag=config.get('Analysis','tag')
        theScale = 1.
        count = (posWeight.GetBinContent(1) - negWeight.GetBinContent(1))
        lumi = float(sample.lumi)
        theScale = lumi*sample.xsec*sample.sf/(count)
        #print("sample: ",sample,"lumi: ",lumi,"xsec: ",sample.xsec,"sample.sf: ",sample.sf,"count: ",count," ---> using scale: ", theScale)
        return theScale

    def get_scale(self, sample, config, lumi = None, count=1):
        return self.get_scale_training(sample, config, lumi, count)

    def get_scale_LHE(self, sample, config, lhe_scale, lumi = None, count=1):
        self.__cachedPath
        posWeight = self.get_weight_histogram(self.__hashDict[sample.name], 'CountPosWeight')  #input.Get('CountPosWeight')
        negWeight = self.get_weight_histogram(self.__hashDict[sample.name], 'CountNegWeight')  #input.Get('CountNegWeight')
        Weight = self.get_weight_histogram(self.__hashDict[sample.name], 'CountWeighted')     #input.Get('CountWeighted')
        countWeightedLHEWeightScale = self.get_weight_histogram(self.__hashDict[sample.name], 'CountWeightedLHEWeightScale')    #input.Get('CountWeightedLHEWeightScale')

        scaled_count = 0
        if lhe_scale == 0:
            scaled_count = countWeightedLHEWeightScale.GetBinContent(0+1)
        elif lhe_scale == 1:
            scaled_count = countWeightedLHEWeightScale.GetBinContent(1+1)
        elif lhe_scale == 2:
            scaled_count = countWeightedLHEWeightScale.GetBinContent(2+1)
        elif lhe_scale == 3:
            scaled_count = countWeightedLHEWeightScale.GetBinContent(3+1)

        count = (posWeight.GetBinContent(1) - negWeight.GetBinContent(1))
        countWeightNoPU = (posWeight.GetBinContent(1) + negWeight.GetBinContent(1))
        countWeightPU = Weight.GetBinContent(1)


        if scaled_count == 0:
            return 0.
        else:
            return (countWeightNoPU/count)*self.get_scale_training(sample, config, lumi, count)*count/(scaled_count*(countWeightNoPU/countWeightPU))


    #Jdef get_cache(self, sample, config):
    ##retrives the cahe __cachedPath and __hashDict
    #self.__cachedPath = config.get('Directories','tmpSamples')
    #source = '%s/%s' %(self.path,sample.get_path)
    #checksum = self.get_checksum(source)
    #theHash = hashlib.sha224('%s_s%s_%s' %(sample,checksum,self.minCut)).hexdigest()
    #self.__hashDict[sample.name] = theHash



    @staticmethod
    def get_checksum(file):
        if 'gsidcap://t3se01.psi.ch:22128' in file:
            srmPath = 'srm://t3se01.psi.ch:8443/srm/managerv2?SFN='
            if TreeCache.get_slc_version() == 'SLC5':
                command = 'lcg-ls -b -D srmv2 -l %s' %file.replace('gsidcap://t3se01.psi.ch:22128/','%s/'%srmPath)
                p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)
                lines = p.stdout.readlines()
                if any('No such' in line for line in lines):
                    print('File not found')
                    print(command)
                line = lines[1].replace('\t* Checksum: ','')
                checksum = line.replace(' (adler32)\n','')
            elif TreeCache.get_slc_version() == 'SLC6':
                command = 'srmls -l %s' %file.replace('gsidcap://t3se01.psi.ch:22128/','%s/'%srmPath)
                p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)
                lines = p.stdout.readlines()
                if any('does not exist' in line for line in lines):
                    print('File not found')
                    print(command)
                checksum = lines[6].replace('- Checksum value:','')
                checksum = checksum.strip()
                #srmPath = 'srm://t3se01.psi.ch'
                #command = 'gfal-sum %s ADLER32' %file.replace('gsidcap://t3se01.psi.ch:22128/','%s/'%srmPath)
                #print(command)
                #p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)
                #lines = p.stdout.readlines()
                #if any('No such' in line for line in lines):
                #    print('File not found')
                #    print(command)
                #checksum = lines[0].split()[1]

        else:
            command = 'md5sum %s' %file
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)
            lines = p.stdout.readlines()
            checksum = lines[0]
        return checksum
    
    @staticmethod
    def file_exists(file):
        print ('Will now check if the file exists')
        print ('=================================\n')

        file_exists = False

        file_dummy = file
        #srmPath = 'srm://t3se01.psi.ch:8443/srm/managerv2?SFN='
        file_dummy = file_dummy.replace('root://t3dcachedb03.psi.ch:1094/','')
        file_dummy = file_dummy.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=','')

        print ('The command is', 'os.path.isfile(',file_dummy,')', os.path.isfile(file_dummy))
        if os.path.isfile(file_dummy):
            print(file_dummy, 'exists.')
            f = ROOT.TFile.Open(file,'read')
            if not f:
                print ('File is null. Gonna redo it.')
                del_protocol = file.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                if '/scratch/' in  del_protocol: command = 'rm %s' %(del_protocol)
                else: command = 'gfal-rm %s' %(del_protocol)
                subprocess.call([command], shell=True)
                print(command)
            elif f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
                print ('f.GetNkeys()',f.GetNkeys(),'f.TestBit(ROOT.TFile.kRecovered)',f.TestBit(ROOT.TFile.kRecovered),'f.IsZombie()',f.IsZombie())
                print ('File', file_dummy, 'already exists but is buggy, gonna delete and rewrite it.')
                del_protocol = file.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                # print('del_protocol',del_protocol)
                if '/scratch/' in  del_protocol: command = 'rm %s' %(del_protocol)
                else: command = 'gfal-rm %s' %(del_protocol)
                subprocess.call([command], shell=True)
                print(command)
            else:
                file_exists = True

        #exist = os.path.exists(file_dummy)
        #print('os.path.exists(',file_dummy,')',exist)
        #return os.path.exists(file_dummy)
        return file_exists


