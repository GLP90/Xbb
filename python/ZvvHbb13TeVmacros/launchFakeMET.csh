#source /afs/pi.infn.it/grid_exp_sw/cms/scripts/setcms.sh
#setenv SCRAM_ARCH="slc5_amd64_gcc462"
#source $VO_CMS_SW_DIR/cmsset_default.sh
#eval `scramv1 runtime -sh`
##eval `cmsenv`

setenv envFolder    ../MCAndDataLinks/
setenv source_      ../MCAndDataLinks/

#/gpfs/ddn/srm/cms/store/user/arizzi/VHBBHeppyV14/QCD_HT100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/*/*/*/tree*.root

setenv QCDHT100     QCD_HT100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8
setenv QCDHT200     QCD_HT200to300_TuneCUETP8M1_13TeV-madgraphMLM-pythia8
setenv QCDHT300     QCD_HT300to500_TuneCUETP8M1_13TeV-madgraphMLM-pythia8
setenv QCDHT500     QCD_HT500to700_TuneCUETP8M1_13TeV-madgraphMLM-pythia8
setenv QCDHT700     QCD_HT700to1000_TuneCUETP8M1_13TeV-madgraphMLM-pythia8
setenv QCDHT1000    QCD_HT1000to1500_TuneCUETP8M1_13TeV-madgraphMLM-pythia8
setenv QCDHT1500    QCD_HT1500to2000_TuneCUETP8M1_13TeV-madgraphMLM-pythia8
setenv QCDHT2000    QCD_HT2000toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8

mkdir $envFolder'/Fake'$QCDHT100
mkdir $envFolder'/Fake'$QCDHT200
mkdir $envFolder'/Fake'$QCDHT300
mkdir $envFolder'/Fake'$QCDHT500
mkdir $envFolder'/Fake'$QCDHT700
mkdir $envFolder'/Fake'$QCDHT1000
mkdir $envFolder'/Fake'$QCDHT1500
mkdir $envFolder'/Fake'$QCDHT2000
mkdir $envFolder'/FakeQCDTest/'

python launchFakeMET.py $source_/$QCDHT100  $envFolder'/Fake'$QCDHT100'/'     >& logFakeQCDHT100 &
python launchFakeMET.py $source_/$QCDHT200  $envFolder'/Fake'$QCDHT200'/'     >& logFakeQCDHT200 &
python launchFakeMET.py $source_/$QCDHT300  $envFolder'/Fake'$QCDHT300'/'     >& logFakeQCDHT300 &
python launchFakeMET.py $source_/$QCDHT500  $envFolder'/Fake'$QCDHT500'/'     >& logFakeQCDHT500 &
python launchFakeMET.py $source_/$QCDHT700  $envFolder'/Fake'$QCDHT700'/'     >& logFakeQCDHT700 &
python launchFakeMET.py $source_/$QCDHT1000 $envFolder'/Fake'$QCDHT1000'/'    >& logFakeQCDHT1000 &
python launchFakeMET.py $source_/$QCDHT1500 $envFolder'/Fake'$QCDHT1500'/'    >& logFakeQCDHT1500 &
python launchFakeMET.py $source_/$QCDHT2000 $envFolder'/Fake'$QCDHT2000'/'    >& logFakeQCDHT2000 &

python launchFakeMET.py $source_/$QCDHT500 $envFolder'/FakeQCDTest/'    >& logFakeQCDTest &


