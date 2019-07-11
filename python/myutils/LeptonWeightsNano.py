#!/usr/bin/env python
import ROOT
import numpy as np
import array
import os
import math
from LeptonSF import LeptonSF

class LeptonWeights(object):

    def __init__(self, channel=''):
        self.channel = channel
        self.lastEntry = -1
        self.branchBuffers = {}
        self.branches = []
        # initialize buffers for new branches 
        if channel == 'Zll' or len(channel)<1:
            for branchName in ['weight_SF_LooseID','weight_SF_LooseISO','weight_SF_LooseIDnISO', 'weight_SF_TRK', 'weight_SF_Lepton', 'eTrigSFWeight_doubleEle80x', 'muTrigSFWeight_doublemu']:
                self.branchBuffers[branchName] = array.array('f', [1.0, 0.0, 0.0])
                self.branches.append({'name': branchName, 'formula': self.getVectorBranch, 'arguments': {'branch': branchName, 'length':3}, 'length': 3})
            for branchName in ['weight_SF_LooseIDnISO_B', 'weight_SF_LooseIDnISO_E']:
                self.branchBuffers[branchName] = array.array('f', [0.0, 0.0])
                self.branches.append({'name': branchName, 'formula': self.getVectorBranch, 'arguments': {'branch': branchName, 'length':2}, 'length': 2})
        if channel == 'Wlv' or channel == 'Zvv' or len(channel)<1:
            for branchName in ['weight_SF_TightID', 'weight_SF_TightISO', 'weight_SF_TightIDnISO', 'weight_SF_TRK', 'weight_SF_Lepton', 'eTrigSFWeight_singleEle80', 'muTrigSFWeight_singlemu']:
                self.branchBuffers[branchName] = array.array('f', [1.0, 0.0, 0.0])
                self.branches.append({'name': branchName, 'formula': self.getVectorBranch, 'arguments': {'branch': branchName, 'length':3}, 'length': 3})
        self.leptonSF = {}

    def customInit(self, initVars):
        self.config = initVars['config']
        self.sample = initVars['sample']

        # don't compute SF for DATA
        if self.sample.isData():
            self.branches = []

    def getBranches(self):
        return self.branches

    # read from buffers which have been filled in processEvent()    
    def getBranch(self, event, arguments=None):
        self.processEvent(event)
        if arguments:
            return self.branchBuffers[arguments][0]

    # read from buffers which have been filled in processEvent()    
    def getVectorBranch(self, event, arguments=None, destinationArray=None):
        self.processEvent(event)
        for i in range(arguments['length']):
            destinationArray[i] =  self.branchBuffers[arguments['branch']][i]

    def computeSF_SingleLep(self, weight_SF):
        '''Combines SF of each leg to compute final event SF'''
        weight_SF[0] = self.weight[0][0]
        weight_SF[1] = self.weight[0][0]-self.weight[0][1]
        weight_SF[2] = self.weight[0][0]+self.weight[0][1]

    def computeSF(self, weight_SF):
        '''Combines SF of each leg to compute final event SF'''
        weight_SF[0] = (self.weight[0][0]*self.weight[1][0])
        weight_SF[1] = ( (self.weight[0][0]-self.weight[0][1])*(self.weight[1][0]-self.weight[1][1]) )
        weight_SF[2] = ( (self.weight[0][0]+self.weight[0][1])*(self.weight[1][0]+self.weight[1][1]) )

    def computeSF_region(self, weight_SF_LowEta, weight_SF_HighEta, lep1_eta, lep2_eta, etacut):
        '''Extact the systematics corresponding to computeSF function in different region of eta'''
        if abs(lep1_eta) < etacut and abs(lep2_eta) < etacut:
            #assign sys
            weight_SF_LowEta[0] = ((self.weight[0][0]-self.weight[0][1])*(self.weight[1][0]-self.weight[1][1]))
            weight_SF_LowEta[1] = ((self.weight[0][0]+self.weight[0][1])*(self.weight[1][0]+self.weight[1][1]))
            #sys are nom value
            weight_SF_HighEta[0] = (self.weight[0][0]*self.weight[1][0])
            weight_SF_HighEta[1] = (self.weight[0][0]*self.weight[1][0])

        elif abs(lep1_eta) > etacut and abs(lep2_eta) > etacut:
            #sys are nom value
            weight_SF_LowEta[0] =  (self.weight[0][0]*self.weight[1][0])
            weight_SF_LowEta[1] =  (self.weight[0][0]*self.weight[1][0])
            #assign sys
            weight_SF_HighEta[0] = ((self.weight[0][0]-self.weight[0][1])*(self.weight[1][0]-self.weight[1][1])) 
            weight_SF_HighEta[1] = ((self.weight[0][0]+self.weight[0][1])*(self.weight[1][0]+self.weight[1][1])) 

        elif abs(lep1_eta) < etacut and abs(lep2_eta) > etacut:
            weight_SF_LowEta[0] =  ((self.weight[0][0]-self.weight[0][1])*self.weight[1][0])
            weight_SF_LowEta[1] =  ((self.weight[0][0]+self.weight[0][1])*self.weight[1][0])
            weight_SF_HighEta[0] = ((self.weight[0][0])*(self.weight[1][0]-self.weight[1][1])) 
            weight_SF_HighEta[1] = ((self.weight[0][0])*(self.weight[1][0]+self.weight[1][1])) 

        elif abs(lep1_eta) > etacut and abs(lep2_eta) < etacut:
            weight_SF_LowEta[0] =  ((self.weight[0][0])*(self.weight[1][0]-self.weight[1][1])) 
            weight_SF_LowEta[1] =  ((self.weight[0][0])*(self.weight[1][0]+self.weight[1][1])) 
            weight_SF_HighEta[0] = ((self.weight[0][0]-self.weight[0][1])*self.weight[1][0])
            weight_SF_HighEta[1] = ((self.weight[0][0]+self.weight[0][1])*self.weight[1][0])

    def computeSF_leg(self, leg):
        #leg is the leg index, can be 0 or 1
        eff_leg = [1.,0.,0.]
        eff_leg[0] = (self.weight[leg][0])
        eff_leg[1] = self.weight[leg][0]-self.weight[leg][1]
        eff_leg[2] = self.weight[leg][0]+self.weight[leg][1]
        return eff_leg

    def computeEventSF_fromleg(self, effleg1, effleg2):
        #returns event efficiency and relative uncertainty
        eff_event = [1.,0.]
        eff_event[0] = ((effleg1[0][0]**2*effleg2[1][0] + effleg1[1][0]**2*effleg2[0][0])/(effleg1[0][0] + effleg1[1][0]))
        #relative uncertainty down
        uncert_down = (abs(((effleg1[0][1]**2*effleg2[1][1] + effleg1[1][1]**2*effleg2[0][1])/(effleg1[0][1] + effleg1[1][1])) - eff_event[0])/eff_event[0])
        #relative uncertainty up
        uncert_up = (abs(((effleg1[0][2]**2*effleg2[1][2] + effleg1[1][2]**2*effleg2[0][2])/(effleg1[0][2] + effleg1[1][2])) - eff_event[0])/eff_event[0])
        eff_event[1]  = (uncert_down+uncert_up)/2.
        return eff_event

    def computeEvenSF_DZ(self, eff):
        eff_event = [1.,0.]
        eff_event[0] = ((eff[0][0]**2 + eff[1][0]**2)/(eff[0][0] + eff[1][0]))
        #relative uncertainty down
        uncert_down = (((eff[0][1]**2 + eff[1][1]**2)/(eff[0][1] + eff[1][1])) - eff_event[0])/eff_event[0]
        #relative uncertainty up
        uncert_up = (((eff[0][2]**2 + eff[1][2]**2)/(eff[0][2] + eff[1][2])) - eff_event[0])/eff_event[0]
        eff_event[1]  = (uncert_down+uncert_up)/2.
        return eff_event

    def getLumiAvrgSF(self, weightLum1, lum1, weightLum2, lum2, weight_SF):
        ##Take SF for two different run categorie and makes lumi average'''

        weight_SF[0] = weightLum1[0]*lum1+weightLum2[0]*lum2
        weight_SF[1] = weightLum1[1]*lum1+weightLum2[1]*lum2
        weight_SF[2] = weightLum1[2]*lum1+weightLum2[2]*lum2

    def computeEff(self, weight_Eff):
        eff1 = []
        eff2 = []
        eff1.append(self.weight[0][0])
        eff1.append(self.weight[0][0]-self.weight[0][1])
        eff1.append(self.weight[0][0]+self.weight[0][1])
        eff2.append(self.weight[1][0])
        eff2.append(self.weight[1][0]-self.weight[1][1])
        eff2.append(self.weight[1][0]+self.weight[1][1])
        weight_Eff[0] = (eff1[0]*(1-eff2[0])*eff1[0] + eff2[0]*(1-eff1[0])*eff2[0] + eff1[0]*eff1[0]*eff2[0]*eff2[0])
        weight_Eff[1] = (eff1[1]*(1-eff2[1])*eff1[1] + eff2[1]*(1-eff1[1])*eff2[1] + eff1[1]*eff1[1]*eff2[1]*eff2[1])
        weight_Eff[2] = (eff1[2]*(1-eff2[2])*eff1[2] + eff2[2]*(1-eff1[2])*eff2[2] + eff1[2]*eff1[2]*eff2[2]*eff2[2])
        return weight_Eff

    # compute all the weights
    def processEvent(self, tree):
        isGoodEvent = True
        currentEntry = tree.GetReadEntry()
        # if current entry has not been processed yet
        if currentEntry != self.lastEntry:
            self.lastEntry = currentEntry
            # ================ Lepton Scale Factors =================
            # For custom made form own JSON files

            if self.channel == 'Zll' or len(self.channel) < 1:
                #Reinitialize all the variables
                for branchName in ['weight_SF_LooseID','weight_SF_LooseISO','weight_SF_LooseIDnISO', 'weight_SF_TRK', 'weight_SF_Lepton', 'eTrigSFWeight_doubleEle80x', 'muTrigSFWeight_doublemu']:
                    self.branchBuffers[branchName][0] = 1.0
                    self.branchBuffers[branchName][1] = 0.0
                    self.branchBuffers[branchName][2] = 0.0
                for branchName in ['weight_SF_LooseIDnISO_B', 'weight_SF_LooseIDnISO_E']:
                    self.branchBuffers[branchName][0] = 0.0
                    self.branchBuffers[branchName][1] = 0.0

                muID_BCDEF = [1.,0.,0.]
                muID_GH = [1.,0.,0.]
                muISO_BCDEF = [1.,0.,0.]
                muISO_GH = [1.,0.,0.]
                muTRK_BCDEF= [1.0,0.,0.]
                muTRK_GH = [1.0,0.,0.]
                btagSF = [1.,0.,0.]
                #for muon trigger
                 #Run BCDEFG
                effDataBCDEFG_leg8 = []
                effDataBCDEFG_leg17= []
                effMCBCDEFG_leg8= []
                effMCBCDEFG_leg17 = []
                 #Run H
                effDataH_leg8 = []
                effDataH_leg17 = []
                effMCH_leg8 = []
                effMCH_leg17 = []
                 #Run H dZ
                effDataH_DZ= []
                effMCH_DZ= []

                wdir = self.config.get('Directories', 'vhbbpath')

                jsons = {
                    #
                    #Muon
                    #
                    #ID and ISO
                    wdir+'/python/json/V25/muon_ID_BCDEFv2.json' : ['MC_NUM_LooseID_DEN_genTracks_PAR_pt_eta', 'abseta_pt_ratio'],
                    wdir+'/python/json/V25/muon_ID_GHv2.json' : ['MC_NUM_LooseID_DEN_genTracks_PAR_pt_eta', 'abseta_pt_ratio'],
                    wdir+'/python/json/V25/muon_ISO_BCDEFv2.json' : ['LooseISO_LooseID_pt_eta', 'abseta_pt_ratio'],
                    wdir+'/python/json/V25/muon_ISO_GHv2.json' : ['LooseISO_LooseID_pt_eta', 'abseta_pt_ratio'],
                    #Tracker
                    wdir+'/python/json/V25/trk_SF_RunBCDEF.json' : ['Graph', 'ratio_eff_eta3_dr030e030_corr'],
                    wdir+'/python/json/V25/trk_SF_RunGH.json' : ['Graph', 'ratio_eff_eta3_dr030e030_corr'],
                    #Trigg
                        #BCDEFG
                    wdir+'/python/json/V25/Data_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg8.json' : ['MC_NUM_hlt_Mu17_Mu8_OR_TkMu8_leg8_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_DATA'],
                    wdir+'/python/json/V25/Data_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg17.json' : ['MC_NUM_hlt_Mu17Mu8_leg17_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_DATA'],
                    wdir+'/python/json/V25/MC_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg8.json' : ['MC_NUM_hlt_Mu17_Mu8_OR_TkMu8_leg8_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_MC'],
                    wdir+'/python/json/V25/MC_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg17.json' : ['MC_NUM_hlt_Mu17Mu8_leg17_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_MC'],
                        #H
                            #no DZ
                    wdir+'/python/json/V25/Data_EfficienciesAndSF_doublehlt_perleg_RunH_leg8.json' : ['MC_NUM_hlt_Mu17_Mu8_OR_TkMu8_leg8_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_DATA'],
                    wdir+'/python/json/V25/Data_EfficienciesAndSF_doublehlt_perleg_RunH_leg17.json' : ['MC_NUM_hlt_Mu17Mu8_leg17_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_DATA'],
                    wdir+'/python/json/V25/MC_EfficienciesAndSF_doublehlt_perleg_RunH_leg8.json' : ['MC_NUM_hlt_Mu17_Mu8_OR_TkMu8_leg8_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_MC'],
                    wdir+'/python/json/V25/MC_EfficienciesAndSF_doublehlt_perleg_RunH_leg17.json' : ['MC_NUM_hlt_Mu17Mu8_leg17_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_MC'],
                            #with DZ
                    wdir+'/python/json/V25/DATA_EfficienciesAndSF_dZ_numH.json' : ['MC_NUM_dZ_DEN_hlt_Mu17_Mu8_OR_TkMu8_loose_PAR_eta1_eta2', 'tag_abseta_abseta_DATA'],
                    wdir+'/python/json/V25/MC_EfficienciesAndSF_dZ_numH.json' : ['MC_NUM_dZ_DEN_hlt_Mu17_Mu8_OR_TkMu8_loose_PAR_eta1_eta2', 'tag_abseta_abseta_MC'],
                    #
                    #Electron
                    #
                    #ID and ISO
                    wdir+'/python/json/V25/EIDISO_ZH_out.json' : ['EIDISO_ZH', 'eta_pt_ratio'],
                    #Tracker
                    wdir+'/python/json/V25/ScaleFactor_etracker_80x.json' : ['ScaleFactor_tracker_80x', 'eta_pt_ratio'],
                    #Trigg
                    wdir+'/python/json/V25/DiEleLeg1AfterIDISO_out.json' : ['DiEleLeg1AfterIDISO', 'eta_pt_ratio'],
                    wdir+'/python/json/V25/DiEleLeg2AfterIDISO_out.json' : ['DiEleLeg2AfterIDISO', 'eta_pt_ratio']
                    }
                for j, name in jsons.iteritems():
                    
                    

                    ####
                    #Check if electron or muon
                    ####

                    Electron_subchannel = False
                    if 'EIDISO_ZH_out' in j or 'ScaleFactor_etracker_80x' in j or 'DiEleLeg1AfterIDISO_out' in j or 'DiEleLeg2AfterIDISO_out' in j:
                    Electron_subchannel = True 

                    if Electron_subchannel = True:
                        vLeptons_pt   = tree.Electron_pt
                        vLeptons_eta  = tree.Electron_eta
                        lepidx = getarr(tree, self.config.get('General', 'eIdx'))
                    else:
                        vLeptons_pt   = tree.Muon_pt
                        vLeptons_eta  = tree.Muon_eta
                        lepidx = getarr(tree, self.config.get('General', 'muIdx'))

                    ###
                    #Check index
                    ###


                    self.weight = []
                    lepCorrIdentifier = j + '_' + name[0] + '_' + name[1]
                    if lepCorrIdentifier not in self.leptonSF:
                        self.leptonSF[lepCorrIdentifier] = LeptonSF(j , name[0], name[1])
                    lepCorr = self.leptonSF[lepCorrIdentifier] 

                    #2-D binned SF
                    if not j.find('trk_SF_Run') != -1 and not j.find('EfficienciesAndSF_dZ_numH') != -1:
                        if 'abseta' in  name[1]:
                            self.weight.append(lepCorr.get_2D(eta=abs(vLeptons_eta[lepidx[0]]), vLeptons_pt[lepidx[0]]))
                            self.weight.append(lepCorr.get_2D(eta=abs(vLeptons_eta[lepidx[1]]), vLeptons_pt[lepidx[1]]))
                        else:
                            self.weight.append(lepCorr.get_2D(eta=vLeptons_eta[lepidx[0]], pt=vLeptons_pt[lepidx[0]]))
                            self.weight.append(lepCorr.get_2D(eta=vLeptons_eta[lepidx[1]], pt=vLeptons_pt[lepidx[1]]))
                    elif not j.find('trk_SF_Run') != -1 and j.find('EfficienciesAndSF_dZ_numH') != -1:
                        self.weight.append(lepCorr.get_2D(vLeptons_eta[lepidx[0]],vLeptons_eta[lepidx[1]]))
                        self.weight.append(lepCorr.get_2D(vLeptons_eta[lepidx[1]], vLeptons_eta[lepidx[0]]))
                    #1-D binned SF
                    else:
                        self.weight.append(lepCorr.get_1D(vLeptons_eta[lepidx[0]]))
                        self.weight.append(lepCorr.get_1D(vLeptons_eta[lepidx[1]]))

                    if tree.Vtype == 0:
                        #IDISO
                        if j.find('muon_ID_BCDEF') != -1:
                            self.computeSF(muID_BCDEF)
                        elif j.find('muon_ID_GH') != -1:
                            self.computeSF(muID_GH)
                        elif j.find('muon_ISO_BCDEF') != -1:
                            self.computeSF(muISO_BCDEF)
                        elif j.find('muon_ISO_GH') != -1:
                            self.computeSF(muISO_GH)
                        #TRK
                        elif j.find('trk_SF_RunBCDEF') != -1:
                            self.computeSF(muTRK_BCDEF)
                        elif j.find('trk_SF_RunGH') != -1:
                            self.computeSF(muTRK_GH)
                        #TRIG
                        elif j.find('EfficienciesAndSF_doublehlt_perleg') != -1:
                                #BCDEFG
                            if   j.find('Data_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg8') != -1:
                                #compute the efficiency for both legs
                                effDataBCDEFG_leg8.append(self.computeSF_leg(0))
                                effDataBCDEFG_leg8.append(self.computeSF_leg(1))
                            elif j.find('Data_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg17') != -1:
                                effDataBCDEFG_leg17.append(self.computeSF_leg(0))
                                effDataBCDEFG_leg17.append(self.computeSF_leg(1))
                            elif j.find('MC_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg8') != -1:
                                effMCBCDEFG_leg8.append(self.computeSF_leg(0))
                                effMCBCDEFG_leg8.append(self.computeSF_leg(1))
                            elif j.find('MC_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg17') != -1:
                                effMCBCDEFG_leg17.append(self.computeSF_leg(0))
                                effMCBCDEFG_leg17.append(self.computeSF_leg(1))
                                #H
                            elif j.find('Data_EfficienciesAndSF_doublehlt_perleg_RunH_leg8') != -1:
                                effDataH_leg8.append(self.computeSF_leg(0))
                                effDataH_leg8.append(self.computeSF_leg(1))
                            elif j.find('Data_EfficienciesAndSF_doublehlt_perleg_RunH_leg17') != -1:
                                effDataH_leg17.append(self.computeSF_leg(0))
                                effDataH_leg17.append(self.computeSF_leg(1))
                            elif j.find('MC_EfficienciesAndSF_doublehlt_perleg_RunH_leg8') != -1:
                                effMCH_leg8.append(self.computeSF_leg(0))
                                effMCH_leg8.append(self.computeSF_leg(1))
                            elif j.find('MC_EfficienciesAndSF_doublehlt_perleg_RunH_leg17') != -1:
                                effMCH_leg17.append(self.computeSF_leg(0))
                                effMCH_leg17.append(self.computeSF_leg(1))
                                #H dZ only
                        elif j.find('DATA_EfficienciesAndSF_dZ_numH') != -1:
                            effDataH_DZ.append(self.computeSF_leg(0))
                            effDataH_DZ.append(self.computeSF_leg(1))
                        elif j.find('MC_EfficienciesAndSF_dZ_numH') != -1:
                            effMCH_DZ.append(self.computeSF_leg(0))
                            effMCH_DZ.append(self.computeSF_leg(1))

                    elif tree.Vtype == 1:
                        #IDISO
                        if j.find('EIDISO_ZH_out') != -1:
                            self.computeSF(self.branchBuffers['weight_SF_LooseIDnISO'])
                            self.computeSF_region(self.branchBuffers['weight_SF_LooseIDnISO_B'], self.branchBuffers['weight_SF_LooseIDnISO_E'], vLeptons_eta[lepidx[0]], vLeptons_eta[lepidx[1]], 1.566)
                        #TRK
                        elif j.find('ScaleFactor_etracker_80x') != -1:
                            self.computeSF(self.branchBuffers['weight_SF_TRK'])
                        #TRIG
                        elif j.find('DiEleLeg1AfterIDISO_out') != -1:
                            eff1 = self.weight[0][0]
                            eff1Up = (self.weight[0][0]+self.weight[0][1])
                            eff1Down = (self.weight[0][0]-self.weight[0][1])
                        elif j.find('DiEleLeg2AfterIDISO_out') != -1:
                            eff2 = self.weight[1][0]
                            eff2Up = (self.weight[1][0]+self.weight[1][1])
                            eff2Down = (self.weight[1][0]-self.weight[1][1])
                #//// from 6ae102d
                if tree.Vtype == 0:
                    #print 'muTRK_BCDEF is', muTRK_BCDEF
                    #print 'muTRK_GH is', muTRK_GH
                    #print 'muID_BCDEF is', muID_BCDEF
                    #print 'muID_GH is', muID_GH
                    #print 'muISO_BCDEF is', muISO_BCDEF
                    #print 'muISO_GH is', muISO_GH

                    #Tracker
                    self.getLumiAvrgSF(muTRK_BCDEF,(20.1/36.4),muTRK_GH,(16.3/36.4),self.branchBuffers['weight_SF_TRK'])
                    #ID and ISO
                    self.getLumiAvrgSF(muID_BCDEF,(20.1/36.4),muID_GH,(16.3/36.4),self.branchBuffers['weight_SF_LooseID'])
                    self.getLumiAvrgSF(muISO_BCDEF,(20.1/36.4),muISO_GH,(16.3/36.4),self.branchBuffers['weight_SF_LooseISO'])

                    self.branchBuffers['weight_SF_LooseIDnISO'][0] = self.branchBuffers['weight_SF_LooseID'][0]*self.branchBuffers['weight_SF_LooseISO'][0]
                    self.branchBuffers['weight_SF_LooseIDnISO'][1] = self.branchBuffers['weight_SF_LooseID'][1]*self.branchBuffers['weight_SF_LooseISO'][1]
                    self.branchBuffers['weight_SF_LooseIDnISO'][2] = self.branchBuffers['weight_SF_LooseID'][2]*self.branchBuffers['weight_SF_LooseISO'][2]
                    #Trigger
                        #BCDEFG no DZ
                    EffData_BCDEFG = [1.0,0.]
                    EffMC_BCDEFG = [1.0,0.]
                    SF_BCDEFG = [1.0,0.,0.]
                    EffData_BCDEFG = self.computeEventSF_fromleg(effDataBCDEFG_leg8,effDataBCDEFG_leg17)
                    EffMC_BCDEFG = self.computeEventSF_fromleg(effMCBCDEFG_leg8,effMCBCDEFG_leg17)
                    SF_BCDEFG[0] =  (EffData_BCDEFG[0]/EffMC_BCDEFG[0])
                    SF_BCDEFG[1] = (1-math.sqrt(EffData_BCDEFG[1]**2+ EffMC_BCDEFG[1]**2))*SF_BCDEFG[0]
                    SF_BCDEFG[2] = (1+math.sqrt(EffData_BCDEFG[1]**2+ EffMC_BCDEFG[1]**2))*SF_BCDEFG[0]
                        #H no DZ
                    EffData_H = [1.0,0.]
                    EffMC_H = [1.0,0.]
                    SF_H = [1.0,0.,0.]
                    EffData_H = self.computeEventSF_fromleg(effDataH_leg8,effDataH_leg17)
                    EffMC_H = self.computeEventSF_fromleg(effMCH_leg8,effMCH_leg17)
                    SF_H[0] =  (EffData_H[0]/EffMC_H[0])
                    SF_H[1] = (1-math.sqrt(EffData_H[1]**2+ EffMC_H[1]**2))*SF_H[0]
                    SF_H[2] = (1+math.sqrt(EffData_H[1]**2+ EffMC_H[1]**2))*SF_H[0]
                        #H DZ SF
                    EffData_DZ = [1.0,0.]
                    EffMC_DZ = [1.0,0.]
                    SF_DZ = [1.0,0.,0.]
                    EffData_DZ = self.computeEvenSF_DZ(effDataH_DZ)
                    EffMC_DZ = self.computeEvenSF_DZ(effMCH_DZ)
                    SF_DZ[0] = (EffData_DZ[0]/EffMC_DZ[0])
                    SF_DZ[1] = (1-math.sqrt(EffData_DZ[1]**2+ EffMC_DZ[1]**2))*SF_DZ[0]
                    SF_DZ[2] = (1+math.sqrt(EffData_DZ[1]**2+ EffMC_DZ[1]**2))*SF_DZ[0]

                    #print 'List of all the double trigger SF + uncert'
                    #print 'SF_BCDEFG:', SF_BCDEFG[0], '+', SF_BCDEFG[1], '-', SF_BCDEFG[2]
                    #print 'SF_H:', SF_H[0], '+', SF_H[1], '-', SF_H[2]
                    #print 'SF_DZ:', SF_DZ[0], '+', SF_DZ[1], '-', SF_DZ[2]
                    #Final weight
                    self.branchBuffers['muTrigSFWeight_doublemu'][0] = (27.221/35.827)*SF_BCDEFG[0] + (8.606/35.827)*SF_H[0]*SF_DZ[0]
                    self.branchBuffers['muTrigSFWeight_doublemu'][1] = (27.221/35.827)*SF_BCDEFG[1] + (8.606/35.827)*SF_H[1]*SF_DZ[1]
                    self.branchBuffers['muTrigSFWeight_doublemu'][2] = (27.221/35.827)*SF_BCDEFG[2] + (8.606/35.827)*SF_H[2]*SF_DZ[2]

                if tree.Vtype == 1:
                    self.branchBuffers['eTrigSFWeight_doubleEle80x'][0] = eff1*(1-eff2)*eff1 + eff2*(1-eff1)*eff2 + eff1*eff1*eff2*eff2
                    self.branchBuffers['eTrigSFWeight_doubleEle80x'][1] = eff1Down*(1-eff2Down)*eff1Down + eff2Down*(1-eff1Down)*eff2Down + eff1Down*eff1Down*eff2Down*eff2Down
                    self.branchBuffers['eTrigSFWeight_doubleEle80x'][2] = eff1Up*(1-eff2Up)*eff1Up + eff2Up*(1-eff1Up)*eff2Up + eff1Up*eff1Up*eff2Up*eff2Up


                #////


                self.branchBuffers['weight_SF_Lepton'][0] = self.branchBuffers['weight_SF_TRK'][0]*self.branchBuffers['weight_SF_LooseIDnISO'][0]
                self.branchBuffers['weight_SF_Lepton'][1] = self.branchBuffers['weight_SF_TRK'][1]*self.branchBuffers['weight_SF_LooseIDnISO'][1]
                self.branchBuffers['weight_SF_Lepton'][2] = self.branchBuffers['weight_SF_TRK'][2]*self.branchBuffers['weight_SF_LooseIDnISO'][2]
                #print "::", tree.Vtype_new, self.branchBuffers['weight_SF_Lepton']
                #print self.branchBuffers
                #raw_input()

            if self.channel == 'Wlv' or self.channel == 'Zvv' or len(self.channel) < 1:

                for branchName in ['weight_SF_TightID', 'weight_SF_TightISO', 'weight_SF_TightIDnISO', 'weight_SF_TRK', 'weight_SF_Lepton', 'eTrigSFWeight_singleEle80', 'muTrigSFWeight_singlemu']:
                    self.branchBuffers[branchName][0] = 1.0
                    self.branchBuffers[branchName][1] = 0.0
                    self.branchBuffers[branchName][2] = 0.0

                if tree.Vtype != 4 and tree.Vtype != 5:
                    #print 'yeaaaaaaaaaaaaaaaaaaaaaah'
                    muID_BCDEF = [1.,0.,0.]
                    muID_GH = [1.,0.,0.]
                    muISO_BCDEF = [1.,0.,0.]
                    muISO_GH = [1.,0.,0.]
                    muTRK_BCDEF= [1.0,0.,0.]
                    muTRK_GH = [1.0,0.,0.]
                    muTrigg_BCDEF = [1.0,0.,0.]
                    muTrigg_GH = [1.0,0.,0.]
                    wdir = self.config.get('Directories', 'vhbbpath')

                    jsons = {
                        #
                        #Muon
                        #
                        #ID and ISO
                        wdir+'/python/json/V25/muon_ID_BCDEFv2.json' : ['MC_NUM_TightID_DEN_genTracks_PAR_pt_eta', 'abseta_pt_ratio'], #eta pt
                        wdir+'/python/json/V25/muon_ID_GHv2.json' : ['MC_NUM_TightID_DEN_genTracks_PAR_pt_eta', 'abseta_pt_ratio'],
                        ###
                        wdir+'/python/json/V25/muon_ISO_BCDEFv2.json' : ['TightISO_TightID_pt_eta', 'abseta_pt_ratio'],
                        wdir+'/python/json/V25/muon_ISO_GHv2.json' : ['TightISO_TightID_pt_eta', 'abseta_pt_ratio'],
                        #Tracker
                        wdir+'/python/json/V25/trk_SF_RunBCDEF.json' : ['Graph', 'ratio_eff_eta3_dr030e030_corr'],
                        wdir+'/python/json/V25/trk_SF_RunGH.json' : ['Graph', 'ratio_eff_eta3_dr030e030_corr'],
                        #Trigg
                        #BCDEF
                        wdir+'/python/json/V25/EfficienciesAndSF_RunBtoF.json' : ['IsoMu24_OR_IsoTkMu24_PtEtaBins', 'abseta_pt_ratio'],
                        #GH
                        wdir+'/python/json/V25/theJSONfile_Period4.json' : ['IsoMu24_OR_IsoTkMu24_PtEtaBins', 'abseta_pt_ratio'],
                        ##
                        ##Electron
                        ##
                        ##ID and ISO (grouped as MVAid for electron)
                        wdir+'/python/json/V25/EIDISO_WH_out.json' : ['EIDISO_WH', 'eta_pt_ratio'],
                        #Tracker
                        wdir+'/python/json/V25/ScaleFactor_etracker_80x.json' : ['ScaleFactor_tracker_80x', 'eta_pt_ratio'],
                        #Trigg
                        wdir+'/python/json/V25/Tight27AfterIDISO_out.json' : ['Tight27AfterIDISO', 'eta_pt_ratio'],
                        }

                    for j, name in jsons.iteritems():

                        self.weight = []
                        lepCorrIdentifier = j + '_' + name[0] + '_' + name[1]
                        if lepCorrIdentifier not in self.leptonSF:
                            self.leptonSF[lepCorrIdentifier] = LeptonSF(j , name[0], name[1])
                        lepCorr = self.leptonSF[lepCorrIdentifier] 

                        #2-D binned SF
                        #print 'vtype is', tree.Vtype
                        #print 'j is',j 
                        if not j.find('trk_SF_Run') != -1:
                            if 'abseta' in  name[1]:
                                self.weight.append(lepCorr.get_2D(vLeptons_pt[lepidx[0]], abs(vLeptons_eta[lepidx[0]]))
                            else:
                                self.weight.append(lepCorr.get_2D(vLeptons_pt[lepidx[0]], vLeptons_eta[lepidx[0]]))
                        ## SF are not applied on "main" electron but on the veto electron
                        #elif j.find('failingVeto_out') != -1 and tree.Vtype == 3:
                        #    # in case no electron has been vetoed, set SF to 1
                        #    if tree.nElectron < 2:
                        #        w = [1., 0]
                        #        self.weight.append(w)
                        #        #self.weight[0][0] = 1.
                        #        #self.weight[0][1] = 0.
                        #    else:
                        #        for i in range(tree.nElectron):
                        #            if i == tree.VElectronIdx: continue #not additional lepton but main lepton
                        #            self.weight.append(lepCorr.get_2D(tree.Electron_pt[i],tree.Electron_eta[i]))
                        #            break
                        #    #print 'nElectron', tree.nElectron
                        #    #print 'weight is', self.weight[0][0]
                        ##1-D binned SF
                        elif j.find('trk_SF_Run') != -1:
                            self.weight.append(lepCorr.get_1D(vLeptons_eta[lepidx[0]]))

                        if tree.Vtype == 2:
                            #Not filling the branches yet because need to separate run BCDEF and GH
                            #IDISO
                            if j.find('muon_ID_BCDEF') != -1:
                                self.computeSF_SingleLep(muID_BCDEF)
                            elif j.find('muon_ID_GH') != -1:
                                self.computeSF_SingleLep(muID_GH)
                            elif j.find('muon_ISO_BCDEF') != -1:
                                self.computeSF_SingleLep(muISO_BCDEF)
                            elif j.find('muon_ISO_GH') != -1:
                                self.computeSF_SingleLep(muISO_GH)
                            #TRK
                            elif j.find('trk_SF_RunBCDEF') != -1:
                                self.computeSF_SingleLep(muTRK_BCDEF)
                            elif j.find('trk_SF_RunGH') != -1:
                                self.computeSF_SingleLep(muTRK_GH)
                            #TRIG
                            elif j.find('EfficienciesAndSF_RunBtoF') != -1:
                                self.computeSF_SingleLep(muTrigg_BCDEF)
                            elif j.find('theJSONfile_Period4') != -1:
                                self.computeSF_SingleLep(muTrigg_GH)
                        elif tree.Vtype == 3:
                            #Here the branches are filled directly
                            #IDISO
                            if j.find('EIDISO_WH_out') != -1:
                                self.computeSF_SingleLep(self.branchBuffers['weight_SF_TightIDnISO'])
                            #TRK
                            elif j.find('ScaleFactor_etracker_80x') != -1:
                                self.computeSF_SingleLep(self.branchBuffers['weight_SF_TRK'])
                            #TRIG
                            elif j.find('Tight27AfterIDISO_out') != -1:
                                self.computeSF_SingleLep(self.branchBuffers['eTrigSFWeight_singleEle80'])
                            ##VETO
                            #elif j.find('failingVeto_out') != -1:
                            #    self.computeSF_SingleLep(self.branchBuffers['eVeto'])

                    #Fill muon triggers
                    if tree.Vtype == 2:
                        #Fill branches for muon
                        #Tracker
                        self.getLumiAvrgSF(muTRK_BCDEF,(20.1/36.4),muTRK_GH,(16.3/36.4),self.branchBuffers['weight_SF_TRK'])
                        #ID and ISO
                        self.getLumiAvrgSF(muID_BCDEF,(20.1/36.4),muID_GH,(16.3/36.4),self.branchBuffers['weight_SF_TightID'])
                        self.getLumiAvrgSF(muISO_BCDEF,(20.1/36.4),muISO_GH,(16.3/36.4),self.branchBuffers['weight_SF_TightISO'])

                        self.branchBuffers['weight_SF_TightIDnISO'][0] = self.branchBuffers['weight_SF_TightID'][0]*self.branchBuffers['weight_SF_TightISO'][0]
                        self.branchBuffers['weight_SF_TightIDnISO'][1] = self.branchBuffers['weight_SF_TightID'][1]*self.branchBuffers['weight_SF_TightISO'][1]
                        self.branchBuffers['weight_SF_TightIDnISO'][2] = self.branchBuffers['weight_SF_TightID'][2]*self.branchBuffers['weight_SF_TightISO'][2]

                        #Trigger
                        self.getLumiAvrgSF(muTrigg_BCDEF,(20.1/36.4),muTrigg_GH,(16.3/36.4),self.branchBuffers['muTrigSFWeight_singlemu'])

                    self.branchBuffers['weight_SF_Lepton'][0] = self.branchBuffers['weight_SF_TRK'][0]*self.branchBuffers['weight_SF_TightIDnISO'][0]
                    self.branchBuffers['weight_SF_Lepton'][1] = self.branchBuffers['weight_SF_TRK'][1]*self.branchBuffers['weight_SF_TightIDnISO'][1]
                    self.branchBuffers['weight_SF_Lepton'][2] = self.branchBuffers['weight_SF_TRK'][2]*self.branchBuffers['weight_SF_TightIDnISO'][2]
        return isGoodEvent
