#!/bin/bash
#====================================================================
#
#        FILE: runAll.sh
#
#       USAGE: runAll.sh sample energy task
#
# DESCRIPTION: Script to be launched in the batch system.
#              Can also be used, with some care, to run locally.
#
#      AUTHOR: VHbb team
#              ETH Zurich
#
#=====================================================================



# fix for python escape sequence bug:
export TERM=""

#Input argument:
sample=$1           # sample you want to run on. It has to match the naming in sample.info.
energy=$2           # sqrt(s) you want to run
task=$3             # the task 
job_id=$4           # needed for train optimisation. @TO FIX: it does not have a unique meaning
additional_arg=$5   # needed for train optimisation. @TO FIX: it does not have a unique meaning
optional_filelist=$6 # needed to run the prep step with limited number of files per job

# echo '1:'${1}' 2:'${2}' 3:'${3}' 4:'${4}' 5:'${5}' 6:'${6}
echo 
echo 'Reading ./'${energy}'config'
echo 'task'$task
echo 

whereToLaunch=`python << EOF 
import os
from myutils import BetterConfigParser
config = BetterConfigParser()
config.read('./${energy}config/paths.ini')
print config.get('Configuration','whereToLaunch')
EOF`
echo 'whereToLaunch= '$whereToLaunch

#-------------------------------------------------
# Read debug variable
#-------------------------------------------------

DEBUG=`python << EOF 
import os
from myutils import BetterConfigParser
config = BetterConfigParser()
config.read('./${energy}config/general.ini')
print config.get('General','Debug')
EOF`

echo "Debug is " $DEBUG

#-------------------------------------------------
# Check the number of input arguments
#-------------------------------------------------

if [[ $DEBUG -eq "True" ]]
  then
  echo ""
  echo "Checking the number of input arguments"
  echo ""
fi

if [ $# -lt 3 ]
    then
    echo "ERROR: You passed " $# "arguments while the script needs at least 3 arguments."
    echo "Exiting..."
    echo " ---------------------------------- "
    echo " Usage : ./runAll.sh sample energy task"
    echo " ---------------------------------- "
    exit
fi

#------------------------------------------------
# get the log dir from the config and create it
#------------------------------------------------
logpath=`python << EOF 
import os
from myutils import BetterConfigParser
config = BetterConfigParser()
config.read('./${energy}config/paths.ini')
print config.get('Directories','logpath')
EOF`
if [ ! -d $logpath ]
    then
    mkdir -p $logpath
fi

#-------------------------------------------------
#Set the environment for the batch job execution
#-------------------------------------------------
if [[ $whereToLaunch != "lxplus" ]]; then
  cd $CMSSW_BASE/src/
  if [[ $whereToLaunch == "pisa" ]]; then
    source /afs/pi.infn.it/grid_exp_sw/cms/scripts/setcms.sh
  else
    source /swshare/psit3/etc/profile.d/cms_ui_env.sh
    export LD_PRELOAD="libglobus_gssapi_gsi_gcc64pthr.so.0":${LD_PRELOAD}
    export LD_LIBRARY_PATH=/swshare/glite/globus/lib/:/swshare/glite/d-cache/dcap/lib64/:$LD_LIBRARY_PATH
  export LD_PRELOAD="libglobus_gssapi_gsi_gcc64pthr.so.0:${LD_PRELOAD}"
  fi

  export SCRAM_ARCH="slc5_amd64_gcc462"
  source $VO_CMS_SW_DIR/cmsset_default.sh
  eval `scramv1 runtime -sh`
  export TMPDIR=$CMSSW_BASE/src/tmp
  #export TMPDIR=/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/tmp
  if ! [ -e $TMPDIR ]; then mkdir $TMPDIR; fi

  cd -   #back to the working dir
fi

MVAList=`python << EOF 
import os
from myutils import BetterConfigParser
config = BetterConfigParser()
config.read('./${energy}config/training.ini')
print config.get('MVALists','List_for_submitscript')
EOF`


#----------------------------------------------
# load from the paths the configs to be used
#----------------------------------------------
input_configs=`python << EOF 
import os
from myutils import BetterConfigParser
config = BetterConfigParser()
config.read('./${energy}config/paths.ini')
print config.get('Configuration','List')
EOF`
required_number_of_configs=7                                             # set the number of required cconfig
input_configs_array=( $input_configs )                                   # create an array to count the number of elements
if [ ${#input_configs_array[*]} -lt $required_number_of_configs ]        # check if the list contains the right number of configs
    then 
    #echo "@ERROR : The number of the elements in the config list is not correct"
    #exit
    echo "@LOG : The number of config files you are using is"
    echo ${#input_configs_array[*]}
fi
configList=${input_configs// / -C ${energy}config\/}                     # replace the spaces with ' -C '
echo "@LOG : The config list you are using is"
echo ${configList}
echo "task is"
echo ${task}


#------------------------------------
#Run the scripts
#------------------------------------

echo "============================"
echo "Will Lauch the script"
echo "============================"
echo "The command is"

if [ $task = "prep" ]; then
    # ./prepare_environment_with_config.py --samples $sample --config ${energy}config/${configList}
#    print "./prepare_environment_with_config.py --samples" $sample "--config "${energy}"config/"${configList}" --config "${energy}"config/samples_nosplit.cfg #sometime"
    echo "./prepare_environment_with_config.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini" #sometime I need this add: please check --config ${energy}
    ./prepare_environment_with_config.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini #sometime I need this add: please check --config ${energy}config/samples_nosplit.cfg
fi
if [ $task = "singleprep" ]; then
    echo './prepare_environment_with_config.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini --filelist "${optional_filelist}"' #sometime I need this add: please check --config ${energy}
    ./prepare_environment_with_config.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini --filelist "${optional_filelist}" #sometime I need this add: please check --config ${energy}config/samples_nosplit.cfg
fi
if [ $task = "mergesingleprep" ]; then
    echo './prepare_environment_with_config.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini --filelist "${optional_filelist}"' #sometime I need this add: please check --config ${energy}
    ./prepare_environment_with_config.py --samples $sample --config ${energy}config/${configList} --config ${energy}config/samples_nosplit.ini --filelist "${optional_filelist}" #sometime I need this add: please check --config ${energy}config/samples_nosplit.cfg
fi
if [ $task = "trainReg" ]; then
    # ./trainRegression.py --config ${energy}config/${configList}
    echo "./trainRegression.py --config ${energy}config/${configList} --config ${energy}config/regression.ini"
    ./trainRegression.py --config ${energy}config/${configList} --config ${energy}config/regression.ini
fi
if [ $task = "sys" ]; then
    echo "./write_regression_systematics.py --samples $sample --config ${energy}config/${configList}"
    ./write_regression_systematics.py --samples $sample --config ${energy}config/${configList}
fi
if [ $task = "reg" ]; then
    ./only_regression.py --samples $sample --config ${energy}config/${configList}
fi
if [ $task = "eval" ]; then
    echo "./evaluateMVA.py --discr $MVAList --samples $sample --config ${energy}config/${configList}"
    ./evaluateMVA.py --discr $MVAList --samples $sample --config ${energy}config/${configList}
fi
if [ $task = "syseval" ]; then
    echo "./write_regression_systematics.py --samples $sample --config ${energy}config/${configList}"
    ./write_regression_systematics.py --samples $sample --config ${energy}config/${configList}
    echo "./evaluateMVA.py --discr $MVAList --samples $sample --config ${energy}config/${configList}"
    ./evaluateMVA.py --discr $MVAList --samples $sample --config ${energy}config/${configList}
fi
if [ $task = "train" ]; then
    echo "./train.py --training $sample --config ${energy}config/${configList} --local True"
    #./train.py --training $sample --config ${energy}config/${configList} --local True
    python train.py --training $sample --config ${energy}config/${configList} --local True
fi
if [ $task = "plot" ]; then
    echo "./tree_stack.py --region $sample --config ${energy}config/${configList}"
    ./tree_stack.py --region $sample --config ${energy}config/${configList}
fi
if [ $task = "dc" ]; then
    echo "./workspace_datacard.py --variable $sample --config ${energy}config/${configList}  --config ${energy}config/datacards.ini"
    ./workspace_datacard.py --variable $sample --config ${energy}config/${configList}  --config ${energy}config/datacards.ini
#> $TMPDIR/out.txt
#cp $TMPDIR/out.txt '~/'

fi
if [ $task = "split" ]; then
    echo "./split_tree.py --samples $sample --config ${energy}config/${configList} --max-events $job_id"
    ./split_tree.py --samples $sample --config ${energy}config/${configList} --max-events $job_id
fi
if [ $task = "stack" ]; then
    echo "./manualStack.py --config ${energy}config/${configList}"
    ./manualStack.py --config ${energy}config/${configList}
fi
if [ $task = "plot_sys" ]; then
    ./plot_systematics.py --config ${energy}config/${configList}
fi
if [ $task = "mva_opt" ]; then
    if [ $# -lt 5 ]
  then
  echo "@ERROR: You passed " $# "arguments while BDT optimisation needs at least 5 arguments."
  echo "Exiting..."
  echo " ---------------------------------- "
  echo " Usage : ./runAll.sh sample energy task jo_id bdt_factory_settings"
  echo " ---------------------------------- "
  exit
    fi
    echo "BDT factory settings"
    echo $additional_arg
    echo "Runnning"
    ./train.py --name ${sample} --training ${job_id} --config ${energy}config/${configList} --setting ${additional_arg} --local False
fi

echo "end runAll.sh"

# rm -rf $TMPDIR
