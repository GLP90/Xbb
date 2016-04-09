import sys,os
import pickle
import ROOT 
from array import array
from printcolor import printc
from BetterConfigParser import BetterConfigParser
from TreeCache import TreeCache
from math import sqrt
from copy import copy
import time

class HistoMaker:
    def __init__(self, samples, path, config, optionsList,GroupDict=None):
        #samples: list of the samples, data and mc
        #path: location of the samples used to perform the plot
        #config: list of the configuration files
        #optionsList: Dictionnary containing information on vars, including the cuts
        #! Read arguments and initialise variables

        print "Start Creating HistoMaker"
        print "=========================\n"
        self.path = path
        self.config = config
        self.optionsList = optionsList
        self.nBins = optionsList[0]['nBins']
        self.lumi=0.
        self.cuts = []
        for options in optionsList:
            self.cuts.append(options['cut'])
        #print "Cuts:",self.cuts
        self.tc = TreeCache(self.cuts,samples,path,config)# created cached tree i.e. create new skimmed trees using the list of cuts
        #print self.cuts
        self.tc = TreeCache(self.cuts,samples,path,config)
        self._rebin = False
        self.mybinning = None
        self.GroupDict=GroupDict
        self.calc_rebin_flag = False
        VHbbNameSpace=config.get('VHbbNameSpace','library')
        ROOT.gSystem.Load(VHbbNameSpace)

        print ""
        print "Done Creating HistoMaker"
        print "========================\n"

    def get_histos_from_tree(self,job,cutOverWrite=None,quick=True):
        start_time = time.time()

        print "=============================================================\n"
        print "THE SAMPLE IS ",job.name
        print "=============================================================\n"

        '''Function that produce the trees from a HistoMaker'''
         
        print "Begin to extract the histos from trees (get_histos_from_tree)"
        print "=============================================================\n"

        if self.lumi == 0: 
            lumi = self.config.get('Plot_general','lumi')
            print("You're trying to plot with no lumi, I will use ",lumi)
            self.lumi = lumi
         
        hTreeList=[]

        #get the conversion rate in case of BDT plots
        TrainFlag = eval(self.config.get('Analysis','TrainFlag'))
        BDT_add_cut='EventForTraining == 0'

        plot_path = self.config.get('Directories','plotpath')
        addOverFlow=eval(self.config.get('Plot_general','addOverFlow'))

        # get all Histos at once
        #print "The tree in the job is ", job.tree
        CuttedTree = self.tc.get_tree(job,'1')# retrieve the cuted tree
        # print 'CuttedTree.GetEntries()',CuttedTree.GetEntries()
#        print 'begin self.optionsList',self.optionsList
        # print 'end self.optionsList'

        #! start the loop over variables (descriebed in options) 
        First_iter = True
        for options in self.optionsList:
            if First_iter: print 'The name of the job is', job.name
            name=job.name
            if self.GroupDict is None:
                group=job.group
            else:
                group=self.GroupDict[job.name]
            treeVar=options['var']
            if First_iter: print("START %s"%treeVar)
            name=options['name']
            # print 'options[\'name\']',options['name']
            if self._rebin or self.calc_rebin_flag:
                nBins = self.nBins
            else:
                nBins = int(options['nBins'])
            xMin=float(options['xMin'])
            xMax=float(options['xMax'])
            weightF=options['weight']
            if cutOverWrite:
                treeCut=cutOverWrite
            else:
                treeCut='%s'%(options['cut'])

            treeCut = "("+treeCut+")&&"+job.addtreecut 
#            print 'job.addtreecut ',job.addtreecut 
            #options
            #print 'treeCut',treeCut
            #print 'weightF',weightF
            
            hTree = ROOT.TH1F('%s'%name,'%s'%name,nBins,xMin,xMax)
            hTree.Sumw2()
            hTree.SetTitle(job.name)
            #print('hTree.name() 1 =',hTree.GetName())
            #print('treeVar 1 =',treeVar)
            drawoption = ''
#            print("START DRAWING")
            if job.type != 'DATA':
              if CuttedTree and CuttedTree.GetEntries():
                if 'BDT' in treeVar or 'bdt' in treeVar: 
                    drawoption = '(%s)*(%s & %s)'%(weightF,BDT_add_cut,treeCut)
                    if First_iter: print "I'm appling: ",BDT_add_cut
                    # drawoption = 'sign(genWeight)*(%s)*(%s & %s)'%(weightF,treeCut,BDT_add_cut)
                    #print drawoption
                else: 
                    drawoption = '(%s)*(%s)'%(weightF,treeCut)
                #print ('Draw: %s>>%s' %(treeVar,name), drawoption, "goff,e")
                if First_iter: print 'drawoptions are', drawoption
                nevents = CuttedTree.Draw('%s>>%s' %(treeVar,name), drawoption, "goff,e")
                if First_iter: print 'Number of events are', nevents
                #print 'nevents:',hTree.GetEntries(),' hTree.name() 2 =',hTree.GetName()
                full=True
                      # if 'RTight' in treeVar or 'RMed' in treeVar: 
                          # drawoption = '(%s)*(%s & %s)'%(weightF,treeCut,BDT_add_cut)
                          # print drawoption
                      # else: 
                          # drawoption = '(%s)*(%s)'%(weightF,treeCut)
                      # print ('Draw: %s>>%s' %(treeVar,name), drawoption, "goff,e")
                      # print
                      # nevent = CuttedTree.Draw('%s>>%s' %(treeVar,name), drawoption, "goff,e")
                      # print name
                      # print('hTree.name() 2 =',hTree.GetName()," nevent=",nevent)
                      # full=True
                # else:
                    # full=False
            elif job.type == 'DATA':
                if options['blind']:
                    lowLimitBlindingMass    = 90
                    highLimitBlindingMass   = 140
                    lowLimitBlindingBDT     = 0
                    lowLimitBlindingDR      = 0.8
                    highLimitBlindingDR     = 1.6
                    if 'H' in treeVar and 'mass' in treeVar:
                        lowLimitBlindingMass =hTree.GetBinLowEdge(hTree.FindBin(lowLimitBlindingMass))
                        highLimitBlindingMass =hTree.GetBinLowEdge(hTree.FindBin(highLimitBlindingMass))+ hTree.GetBinWidth(hTree.GetBin(highLimitBlindingMass))
                        veto = ("(%s <%s || %s > %s)" %(treeVar,lowLimitBlindingMass,treeVar,highLimitBlindingMass))
                        if First_iter: print "Using veto:",veto
                        CuttedTree.Draw('%s>>%s' %(treeVar,name),veto +'&'+' %(cut)s' %options, "goff,e")
                    elif 'BDT' in treeVar or 'bdt' in treeVar or 'nominal' in treeVar in treeVar:
                        lowLimitBlindingBDT = hTree.GetBinLowEdge(hTree.FindBin(lowLimitBlindingBDT))
                        veto = "(%s <%s)" %(treeVar,lowLimitBlindingBDT)
                        if First_iter: print "Using veto:",veto
                        CuttedTree.Draw('%s>>%s' %(treeVar,name),veto +'&'+' %(cut)s'%options, "goff,e")
                    elif 'dR' in treeVar and 'H' in treeVar:
                        lowLimit   = hTree.GetBinLowEdge(hTree.FindBin(lowLimitBlindingDR))
                        highLimit  = hTree.GetBinLowEdge(hTree.FindBin(highLimitBlindingDR))
                        veto = ("(%s <%s || %s > %s)" %(treeVar,lowLimitBlindingMass,treeVar,highLimitBlindingMass))
                        if First_iter: print "Using veto:",veto
                        CuttedTree.Draw('%s>>%s' %(treeVar,name),veto +'&'+' %(cut)s'%options, "goff,e")
                    else:
                        CuttedTree.Draw('%s>>%s' %(treeVar,name),'%s' %treeCut, "goff,e")
                else:
                    if First_iter: print 'DATA drawoptions', '%s>>%s' %(treeVar,name),'%s' %treeCut
                    CuttedTree.Draw('%s>>%s' %(treeVar,name),'%s' %treeCut, "goff,e")
                full = True
            first_iter = False
            # if full:
                # hTree = ROOT.gDirectory.Get(name)
                # print('histo1',ROOT.gDirectory.Get(name))
            # else:
                # hTree = ROOT.TH1F('%s'%name,'%s'%name,nBins,xMin,xMax)
                # hTree.Sumw2()
                # print('histo2',ROOT.gDirectory.Get(name))
#            print("END DRAWING")
#            print("START RESCALE")
            # if full: print 'hTree',hTree.GetName()
              
            if job.type != 'DATA':
                if 'BDT' in treeVar or 'bdt' in treeVar:
                    if TrainFlag:
                        MC_rescale_factor=2. ##FIXME## only dataset used for training must be rescaled!!
                        print 'I RESCALE BY 2.0'
                    else: 
                        MC_rescale_factor = 1.
                    ScaleFactor = self.tc.get_scale(job,self.config,self.lumi)*MC_rescale_factor
                else: 
                    ScaleFactor = self.tc.get_scale(job,self.config,self.lumi)
                if ScaleFactor != 0:
                    hTree.Scale(ScaleFactor)
                print '\t-->import %s\t Integral: %s'%(job.name,hTree.Integral())
                print("job:",job.name," ScaleFactor=",ScaleFactor)
                print("END RESCALE")
                print("START addOverFlow")
            if addOverFlow:
                uFlow = hTree.GetBinContent(0)+hTree.GetBinContent(1)
                oFlow = hTree.GetBinContent(hTree.GetNbinsX()+1)+hTree.GetBinContent(hTree.GetNbinsX())
                uFlowErr = ROOT.TMath.Sqrt(ROOT.TMath.Power(hTree.GetBinError(0),2)+ROOT.TMath.Power(hTree.GetBinError(1),2))
                oFlowErr = ROOT.TMath.Sqrt(ROOT.TMath.Power(hTree.GetBinError(hTree.GetNbinsX()),2)+ROOT.TMath.Power(hTree.GetBinError(hTree.GetNbinsX()+1),2))
                hTree.SetBinContent(1,uFlow)
                hTree.SetBinContent(hTree.GetNbinsX(),oFlow)
                hTree.SetBinError(1,uFlowErr)
                hTree.SetBinError(hTree.GetNbinsX(),oFlowErr)
            hTree.SetDirectory(0)
#            print("STOP addOverFlow")
#            print("START rebin")
            gDict = {}
            if self._rebin:
                gDict[group] = self.mybinning.rebin(hTree)
                del hTree
            else: 
                #print 'not rebinning %s'%job.name 
                gDict[group] = hTree
#            print("STOP %s"%treeVar)
            hTreeList.append(gDict)
            First_iter = False
        if CuttedTree: CuttedTree.IsA().Destructor(CuttedTree)
        del CuttedTree
        print "Finished to extract the histos from trees (get_histos_from_tree)"
        print "================================================================\n"
        print "get_histos_from_tree DONE for ",job.name," in ", str(time.time() - start_time)," s."
        return hTreeList
       
    @property
    def rebin(self):
        return self._rebin

    @property
    def rebin(self, value):
        if self._rebin and value:
            return True
        elif self._rebin and not value:
            self.nBins = self.norebin_nBins
            self._rebin = False
        elif not self._rebin and value:
            if self.mybinning is None:
                raise Exception('define rebinning first')
            else:
                self.nBins = self.rebin_nBins
                self._rebin = True
                return True
        elif not self._rebin and not self.value:
            return False

    def calc_rebin(self, bg_list, nBins_start=1000, tolerance=0.25):
        #print "START calc_rebin"
        self.calc_rebin_flag = True
        self.norebin_nBins = copy(self.nBins)
        self.rebin_nBins = nBins_start
        self.nBins = nBins_start
        i=0
        #add all together:
        print '\n\t...calculating rebinning...'
        for job in bg_list:
            #print "job",job
            htree = self.get_histos_from_tree(job)[0].values()[0]
            print "Integral",job,htree.Integral()
            if not i:
                totalBG = copy(htree)
            else:
                totalBG.Add(htree,1)
            del htree
            i+=1
        ErrorR=0
        ErrorL=0
        TotR=0
        TotL=0
        binR=self.rebin_nBins
        binL=1
        rel=1.0
        #print "START loop from right"
        #print "totalBG.Draw("","")",totalBG.Integral()
        #---- from right
        while rel > tolerance:
            TotR+=totalBG.GetBinContent(binR)
            ErrorR=sqrt(ErrorR**2+totalBG.GetBinError(binR)**2)
            binR-=1
            # print 'is this loop infinite ?'
            # print "TotR",TotR
            # print "ErrorR",ErrorR
            # print "rel",rel
            if not TotR == 0 and not ErrorR == 0:
                rel=ErrorR/TotR
                print rel
        #print 'upper bin is %s'%binR
        print "END loop from right"

        #---- from left
        rel=1.0
        print "START loop from left"
        while rel > tolerance:
            TotL+=totalBG.GetBinContent(binL)
            ErrorL=sqrt(ErrorL**2+totalBG.GetBinError(binL)**2)
            binL+=1
            if not TotL == 0 and not ErrorL == 0:
                rel=ErrorL/TotL
                #print rel
        #it's the lower edge
        print "STOP loop from left"
        binL+=1
        #print 'lower bin is %s'%binL

        inbetween=binR-binL
        stepsize=int(inbetween)/(int(self.norebin_nBins)-2)
        modulo = int(inbetween)%(int(self.norebin_nBins)-2)

        #print 'stepsize %s'% stepsize
        #print 'modulo %s'%modulo
        binlist=[binL]
        for i in range(0,int(self.norebin_nBins)-3):
            binlist.append(binlist[-1]+stepsize)
        binlist[-1]+=modulo
        binlist.append(binR)
        binlist.append(self.rebin_nBins+1)
        #print 'binning set to %s'%binlist
        #print "START REBINNER"
        self.mybinning = Rebinner(int(self.norebin_nBins),array('d',[-1.0]+[totalBG.GetBinLowEdge(i) for i in binlist]),True)
        self._rebin = True
        print '\t > rebinning is set <\n'

    @staticmethod
    def orderandadd(histo_dicts,setup):
        '''
        Setup is defined in the plot conf file
        histo_dicts contains an array of dictionnary
        '''

        from array import array
        doubleVariable = array('d',[0])
        
        #print "Start orderandadd"
        #print "=================\n"
        #print "Input dict is", histo_dicts

        ordered_histo_dict = {}
        #print "orderandadd-setup",setup
        #print "orderandadd-histo_dicts",histo_dicts
        for sample in setup:
            nSample = 0
            for histo_dict in histo_dicts:
                if histo_dict.has_key(sample):
                    integral = histo_dict[sample].IntegralAndError(0,histo_dict[sample].GetNbinsX(),doubleVariable)
                    error = doubleVariable[0]
                    entries = histo_dict[sample].GetEntries()
                    subsamplename = histo_dict[sample].GetTitle()
                    if nSample == 0:
                        ordered_histo_dict[sample] = histo_dict[sample].Clone()
                    else:
                        ordered_histo_dict[sample].Add(histo_dict[sample])
                    printc('magenta','','\t--> added %s to %s Integral: %s Entries: %s Error: %s'%(subsamplename,sample,integral,entries,error))
                    nSample += 1
        del histo_dicts
        #print "Output dict is", ordered_histo_dict
        return ordered_histo_dict 


class Rebinner:
    def __init__(self,nBins,lowedgearray,active=True):
        self.lowedgearray=lowedgearray
        self.nBins=nBins
        self.active=active
    def rebin(self, histo):
        if not self.active: return histo
        #print histo.Integral()
        ROOT.gDirectory.Delete('hnew')
        histo.Rebin(self.nBins,'hnew',self.lowedgearray)
        binhisto=ROOT.gDirectory.Get('hnew')
        #print binhisto.Integral()
        newhisto=ROOT.TH1F('new','new',self.nBins,self.lowedgearray[0],self.lowedgearray[-1])
        newhisto.Sumw2()
        for bin in range(1,self.nBins+1):
            newhisto.SetBinContent(bin,binhisto.GetBinContent(bin))
            newhisto.SetBinError(bin,binhisto.GetBinError(bin))
        newhisto.SetName(binhisto.GetName())
        newhisto.SetTitle(binhisto.GetTitle())
        #print newhisto.Integral()
        del histo
        del binhisto
        return copy(newhisto)
