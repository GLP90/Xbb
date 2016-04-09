import os,sys,subprocess

#BDT_list = ['ZllBDT_highVpt']
#BDT_list = ['BDT_SCAN_NTrees_200_nEventsMin_200_Zmm_highVpt',
#    'BDT_SCAN_NTrees_200_nEventsMin_300_Zmm_highVpt',
#    'BDT_SCAN_NTrees_300_nEventsMin_200_Zmm_highVpt',
#    'BDT_SCAN_NTrees_300_nEventsMin_300_Zmm_highVpt',]
#BDT_list
BDT_list = ['BDT_SCAN_NTrees_50_nEventsMin_50_Zmm_highVpt','BDT_SCAN_NTrees_50_nEventsMin_100_Zmm_highVpt','BDT_SCAN_NTrees_50_nEventsMin_150_Zmm_highVpt','BDT_SCAN_NTrees_50_nEventsMin_200_Zmm_highVpt','BDT_SCAN_NTrees_50_nEventsMin_250_Zmm_highVpt','BDT_SCAN_NTrees_50_nEventsMin_300_Zmm_highVpt','BDT_SCAN_NTrees_50_nEventsMin_350_Zmm_highVpt','BDT_SCAN_NTrees_50_nEventsMin_400_Zmm_highVpt','BDT_SCAN_NTrees_100_nEventsMin_50_Zmm_highVpt','BDT_SCAN_NTrees_100_nEventsMin_100_Zmm_highVpt','BDT_SCAN_NTrees_100_nEventsMin_150_Zmm_highVpt','BDT_SCAN_NTrees_100_nEventsMin_200_Zmm_highVpt','BDT_SCAN_NTrees_100_nEventsMin_250_Zmm_highVpt','BDT_SCAN_NTrees_100_nEventsMin_300_Zmm_highVpt','BDT_SCAN_NTrees_100_nEventsMin_350_Zmm_highVpt','BDT_SCAN_NTrees_100_nEventsMin_400_Zmm_highVpt','BDT_SCAN_NTrees_200_nEventsMin_50_Zmm_highVpt','BDT_SCAN_NTrees_200_nEventsMin_100_Zmm_highVpt','BDT_SCAN_NTrees_200_nEventsMin_150_Zmm_highVpt','BDT_SCAN_NTrees_200_nEventsMin_200_Zmm_highVpt','BDT_SCAN_NTrees_200_nEventsMin_250_Zmm_highVpt','BDT_SCAN_NTrees_200_nEventsMin_300_Zmm_highVpt','BDT_SCAN_NTrees_200_nEventsMin_350_Zmm_highVpt','BDT_SCAN_NTrees_200_nEventsMin_400_Zmm_highVpt','BDT_SCAN_NTrees_300_nEventsMin_50_Zmm_highVpt','BDT_SCAN_NTrees_300_nEventsMin_100_Zmm_highVpt','BDT_SCAN_NTrees_300_nEventsMin_150_Zmm_highVpt','BDT_SCAN_NTrees_300_nEventsMin_200_Zmm_highVpt','BDT_SCAN_NTrees_300_nEventsMin_250_Zmm_highVpt','BDT_SCAN_NTrees_300_nEventsMin_300_Zmm_highVpt','BDT_SCAN_NTrees_300_nEventsMin_350_Zmm_highVpt','BDT_SCAN_NTrees_300_nEventsMin_400_Zmm_highVpt','BDT_SCAN_NTrees_400_nEventsMin_50_Zmm_highVpt','BDT_SCAN_NTrees_400_nEventsMin_100_Zmm_highVpt','BDT_SCAN_NTrees_400_nEventsMin_150_Zmm_highVpt','BDT_SCAN_NTrees_400_nEventsMin_200_Zmm_highVpt','BDT_SCAN_NTrees_400_nEventsMin_250_Zmm_highVpt','BDT_SCAN_NTrees_400_nEventsMin_300_Zmm_highVpt','BDT_SCAN_NTrees_400_nEventsMin_350_Zmm_highVpt','BDT_SCAN_NTrees_400_nEventsMin_400_Zmm_highVpt','BDT_SCAN_NTrees_500_nEventsMin_50_Zmm_highVpt','BDT_SCAN_NTrees_500_nEventsMin_100_Zmm_highVpt','BDT_SCAN_NTrees_500_nEventsMin_150_Zmm_highVpt','BDT_SCAN_NTrees_500_nEventsMin_200_Zmm_highVpt','BDT_SCAN_NTrees_500_nEventsMin_250_Zmm_highVpt','BDT_SCAN_NTrees_500_nEventsMin_300_Zmm_highVpt','BDT_SCAN_NTrees_500_nEventsMin_350_Zmm_highVpt','BDT_SCAN_NTrees_500_nEventsMin_400_Zmm_highVpt','BDT_SCAN_NTrees_600_nEventsMin_50_Zmm_highVpt','BDT_SCAN_NTrees_600_nEventsMin_100_Zmm_highVpt','BDT_SCAN_NTrees_600_nEventsMin_150_Zmm_highVpt','BDT_SCAN_NTrees_600_nEventsMin_200_Zmm_highVpt','BDT_SCAN_NTrees_600_nEventsMin_250_Zmm_highVpt','BDT_SCAN_NTrees_600_nEventsMin_300_Zmm_highVpt','BDT_SCAN_NTrees_600_nEventsMin_350_Zmm_highVpt','BDT_SCAN_NTrees_600_nEventsMin_400_Zmm_highVpt','BDT_SCAN_NTrees_700_nEventsMin_50_Zmm_highVpt','BDT_SCAN_NTrees_700_nEventsMin_100_Zmm_highVpt','BDT_SCAN_NTrees_700_nEventsMin_150_Zmm_highVpt','BDT_SCAN_NTrees_700_nEventsMin_200_Zmm_highVpt','BDT_SCAN_NTrees_700_nEventsMin_250_Zmm_highVpt','BDT_SCAN_NTrees_700_nEventsMin_300_Zmm_highVpt','BDT_SCAN_NTrees_700_nEventsMin_350_Zmm_highVpt','BDT_SCAN_NTrees_700_nEventsMin_400_Zmm_highVpt','BDT_SCAN_NTrees_800_nEventsMin_50_Zmm_highVpt','BDT_SCAN_NTrees_800_nEventsMin_100_Zmm_highVpt','BDT_SCAN_NTrees_800_nEventsMin_150_Zmm_highVpt','BDT_SCAN_NTrees_800_nEventsMin_200_Zmm_highVpt','BDT_SCAN_NTrees_800_nEventsMin_250_Zmm_highVpt','BDT_SCAN_NTrees_800_nEventsMin_300_Zmm_highVpt','BDT_SCAN_NTrees_800_nEventsMin_350_Zmm_highVpt','BDT_SCAN_NTrees_800_nEventsMin_400_Zmm_highVpt','BDT_SCAN_NTrees_900_nEventsMin_50_Zmm_highVpt','BDT_SCAN_NTrees_900_nEventsMin_100_Zmm_highVpt','BDT_SCAN_NTrees_900_nEventsMin_150_Zmm_highVpt','BDT_SCAN_NTrees_900_nEventsMin_200_Zmm_highVpt','BDT_SCAN_NTrees_900_nEventsMin_250_Zmm_highVpt','BDT_SCAN_NTrees_900_nEventsMin_300_Zmm_highVpt','BDT_SCAN_NTrees_900_nEventsMin_350_Zmm_highVpt','BDT_SCAN_NTrees_900_nEventsMin_400_Zmm_highVpt','BDT_SCAN_NTrees_10000_nEventsMin_50_Zmm_highVpt','BDT_SCAN_NTrees_10000_nEventsMin_100_Zmm_highVpt','BDT_SCAN_NTrees_10000_nEventsMin_150_Zmm_highVpt','BDT_SCAN_NTrees_10000_nEventsMin_200_Zmm_highVpt','BDT_SCAN_NTrees_10000_nEventsMin_250_Zmm_highVpt','BDT_SCAN_NTrees_10000_nEventsMin_300_Zmm_highVpt','BDT_SCAN_NTrees_10000_nEventsMin_350_Zmm_highVpt','BDT_SCAN_NTrees_10000_nEventsMin_400_Zmm_highVpt']



max_running_processes = 3
waiting_time_before_retry = 60 # in seconds

##################################################
# use appropriate tag according to $USER
input_folder = 'GaelZllHbb13TeV'
user = subprocess.Popen("echo $USER", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read()
if 'perrozzi' in user:
    input_folder = 'LucaZllHbb13TeV'
    print 'ciao perrozzi'
##################################################

# create log folder if needed
if not os.path.isdir("./logs"): os.system("mkdir logs")

# loop over bdt points
for BDT_point in BDT_list:
    print 'BDT_point is', BDT_point
    # get the number of running processes
    command = 'ps aux | grep '+user.strip("\n")+' | grep train | grep runAll.sh | wc -l'
    print 'before running',BDT_point,'checking running trainings with the string',command
    running_trainings = int(subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read())/2
    print 'running_trainings are',running_trainings
    # submit a bdt point
    #subprocess.Popen('cd ..; sh runAll.sh '+BDT_point+' '+input_folder+' train 2>&1 > ZllHbb13TeVmacros/logs/'+BDT_point+'.log; cd - &', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.system('sh runAll.sh '+BDT_point+' '+input_folder+' train 2>&1 > /dev/null &')
    # wait if too many bdt points are running
    while running_trainings > max_running_processes:
        running_trainings = int(subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read())/2
        print 'running_trainings',running_trainings,'waiting',waiting_time_before_retry,'seconds before to retry'
        os.system('sleep '+str(waiting_time_before_retry))

