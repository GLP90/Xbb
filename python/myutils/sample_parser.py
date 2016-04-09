import os, sys, warnings
from copy import copy
from optparse import OptionParser
from BetterConfigParser import BetterConfigParser
from samplesclass import Sample

def findnth(haystack, needle, n):
        parts= haystack.split(needle, n+1)
        if len(parts)<=n+1:
            return -1
        return len(haystack)-len(parts[-1])-len(needle)


def test_samples(run_on_fileList,__fileslist,config_sections):
        for _listed_file,_config_entry in map(None,__fileslist,config_sections): # loop in both, fileList and config
                if( run_on_fileList and _listed_file == None ): # check the option to know whether to run in fileList mode or in config mode
                        return False
                elif( (not run_on_fileList) and _config_entry == None ):
                        return False
                else: return True

def check_correspondency(sample,list,config):
        '''Check the samples that are available in the PREPin directory and in the samples_nosplit file '''
        if not any( sample in file for file in list ):
                warnings.warn('@INFO: Sample %s is NOT! present'%(config.get(sample,'sampleName')))


class ParseInfo:
    '''Class containing a list of Sample. Is filled during the prep stage.'''
    def __init__(self,samples_config,samples_path):
        '''
        Methode filling a list of Sample "self._samplelist = []" contained in the class. 
        "sample_path" contains the path where the samples are stored (PREPin). 
        "samples_config" is the "samples_nosplit.cfg" file. Depending of the variable "run_on_files" defined in "samples_nosplit.cfg", 
        the sample list are generated from the input folder (PREPin) or the list in "samples_nosplit.cfg" '''
        
        print "Start getting infos on all the samples (ParseInfo)"
        print "==================================================\n"
        print 'samples_config is', samples_config
        try:
            os.stat(samples_config)
        except:
            raise Exception('config file is wrong/missing')
          
        if '/pnfs/psi.ch/cms/' in samples_path:

            T3 = True
            _,p2=samples_path.split('/pnfs/')
            t3_path = '/pnfs/'+p2.strip('\n')
        else:
            T3 = False

        config = BetterConfigParser()
        config.read(samples_config)

        newprefix=config.get('General','newprefix')
        lumi=float(config.get('General','lumi'))
        weightexpression=config.get('General','weightexpression')

        self._samplelist = []

        #!! Store the list of input samples in __fileslist. Reads them directly from the folder defined in PREPin  
        self.__fileslist=[]
        # print 'T3',T3,'samples_path',samples_path,'t3_path',t3_path
        if T3:
            ls = os.popen("ls "+t3_path)
        else:
            ls = os.popen("ls "+samples_path)
    
  #print 'will start the loop over the lines.'
  #print ls.read()
        for line in ls.readlines():
    #print 'loop over the lines'
                if('.root' in line):
                        truncated_line = line[line.rfind('/')+1:]
                        _p = findnth(truncated_line,'.',2)
                        self.__fileslist.append(truncated_line[_p+1:truncated_line.rfind('.')])
      #print 'added a new line !'

        print '@DEBUG: ' + str(self.__fileslist)

  #Deleteme: Do a loop to check on __fileslist
  #Start the loop
  #for i in range(0,len(self.__fileslist)):
    #print 'Is the ',i ,'th file None ? Answer:', (self.__fileslist[i] == None) 

  #End Deleteme

        run_on_fileList = eval(config.get('Samples_running','run_on_fileList'))#Evaluate run_on_fileList from samples_nosplit.cfg 

  #print 'Is Sample None ? Answer: ', (self.__fileslist == None)

        if( not test_samples(run_on_fileList,self.__fileslist,config.sections()) ): # stop if it finds None as sample
                sys.exit('@ERROR: Sample == None. Check RunOnFileList flag in section General, the sample_config of the sample directory.')

        #!! Start to loop over the samples. If run_on_files list is true, use the sample from the PREPin folder (_listed_file). 
  #!! Else use the sample from  samples_nosplit.cfg (_config_entry).
        #!! The sample description from samples_nosplit.cfg are then applied.
        for _listed_file,_config_entry in map(None,self.__fileslist,config.sections()):
            if( run_on_fileList ): 
                _sample = _listed_file
                self._list = self.__fileslist
            else:
                _sample = _config_entry
                self._list = config.sections()

            sample = self.checkSplittedSample(_sample)#Check if is splitted and remove the _
            if not config.has_option(sample,'sampleName'): continue #Check if the sample has the infile parameter. If not skip
            infile = _sample
            # print 'infile',infile
            sampleName = config.get(sample,'sampleName')
            
            check_correspondency(sample,self._list,config)#Check if the sample exists, not fully understood yet                    
            
            #Initialize samplecalss element
            sampleType = config.get(sample,'sampleType')
            cut = config.get(sample, 'cut')

      #fill the sample
            newsample = Sample(sampleName,sampleType)
            newsample.addtreecut = cut
            newsample.identifier=infile
            newsample.weightexpression=weightexpression
            newsample.lumi=lumi
            newsample.prefix=newprefix
            
      #add and fills all the subsamples
            if eval(config.get(sample,'subsamples')):
                subnames = eval((config.get(sample, 'subnames')))
                subcuts = eval((config.get(sample, 'subcuts')))
                subgroups = eval((config.get(sample,'sampleGroup')))
                if sampleType != 'DATA':
                    subxsecs = eval((config.get(sample, 'xSec')))
                    subsfs = eval((config.get(sample, 'SF')))
                newsamples = []
                for i,cut in enumerate(subcuts):
                    newsubsample = copy(newsample)
                    newsubsample.subsample = True
                    newsubsample.name = subnames[i]
                    newsubsample.subcut = subcuts[i]
                    newsubsample.group = subgroups[i]
                    if sampleType != 'DATA':
                        newsubsample.sf = float(subsfs[i])
                        newsubsample.xsec = float(subxsecs[i])
                    newsamples.append(newsubsample)
                self._samplelist.extend(newsamples)
                self._samplelist.append(newsample)
            else:
                if sampleType != 'DATA':
                    newsample.xsec = eval((config.get(sample,'xSec')))    
                    newsample.sf = eval((config.get(sample, 'SF')))
                newsample.group = config.get(sample,'sampleGroup')
                self._samplelist.append(newsample)
        print "Finished getting infos on all the samples (ParseInfo)"
        print "=====================================================\n"

    def __iter__(self):
        for sample in self._samplelist:
            if sample.active:
                yield sample

    def get_sample(self, samplename):
        '''return the sample whose name matches the sample.name'''
        for sample in self._samplelist:
            if sample.name == samplename:
                return sample
        return None
    
    def get_samples(self, samplenames):
        '''Samplenames is list of the samples names. Returns a list of samples corresponding to the names'''
        samples = []
        thenames = []
        #for splitted samples use the identifier. There is always only one. if list, they are all true
        if (len(samplenames)>0 and self.checkSplittedSampleName(samplenames[0])):
          print "The samples is splitted"
          for sample in self._samplelist:
                  if (sample.subsample): continue #avoid multiple submissions from subsamples
                  print '@DEBUG: samplenames ' + samplenames[0]
                  print '@DEBUG: sample identifier ' + sample.identifier
                  if sample.identifier == samplenames[0]:
                          samples.append(sample)
                          thenames.append(sample.name)
        #else check the name
        else:
                for sample in self._samplelist:
                  if not isinstance(samplenames, (list, tuple)): samplenames = samplenames.split(',')
                  for samplename in samplenames:
                        # print "get_samples sample is", sample ,'samplename',samplename
                        if sample.name == samplename:
                                # print 'matched sample.name',sample.name
                                #if (sample.subsample): continue #avoid multiple submissions from subsamples
                                samples.append(sample)
                                thenames.append(sample.name)
        return samples


    #it checks whether filename is a splitted sample or is a pure samples and returns the file name without the _#
    def checkSplittedSample(self, filename):
            try:
                    isinstance( eval(filename[filename.rfind('_')+1:] ) , int )
                    print '@DEBUG: fileName in CHECKSPLITTEDSAMPLE : ' + filename
                    print '@DEBUG: return in CHECKSPLITTEDSAMPLE : ' + filename[:filename.rfind('_')]
                    return filename[:filename.rfind('_')]
            except:
                    return filename

    #bool
    def checkSplittedSampleName(self,filename):
            print '### CHECKSPLITTEDSAMPLENAME ###',filename
            # if there is an underscore in the filename
            if ( filename.rfind('_') > 0. ) :
                    try:
                            return isinstance( eval(filename[filename.rfind('_')+1:] ) , int )
                    except:
                            return False
            else:
                    return False
            
