#!/usr/bin/env python

import argparse
import getpass
import os
import re
import shutil
import subprocess
import sys
import time

import ROOT
ROOT.gROOT.SetBatch(True)

import myutils


def parse_command_line(argv):

    if argv is None:
        argv = sys.argv[1:]

    tasks = [
        'prep', 'singleprep', 'mergesingleprep', 'trainReg', 'reg', 'eval', 'singleeval', 'mergesingleeval', 'sys', 'singlesys',
        'mergesinglesys', 'syseval', 'train', 'plot', 'dc', 'split', 'stack', 'plot_sys', 'mva_opt', 'mva_opt_eval', 'mva_opt_dc'
    ]

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'tag',
        help='The analysis configuration tag, e.g. "13TeV" to use the configuration files in "13TeVconfig".'
    )
    parser.add_argument(
        'task', choices=tasks, metavar='task',
        help='The task to perform. Allowed values are {}.'.format(', '.join(tasks))
    )
    parser.add_argument(
        '-s', '--samples', nargs='*', default=[],
        help='The samples to run on.'
    )
    parser.add_argument(
        '-t', '--tagdir', default='',
        help='Creates or uses an existing output directory with the specified tag.'
    )
    parser.add_argument(
        '-n', '--nsplit', type=int, default=-1,
        help='The number of events per file when splitting a sample or the number of files per job for the single file workflow.'
    )
    parser.add_argument(
        '-p', '--philipp-love-progress-bars', action='store_true',
        help='If you share the love of Philipp...'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='Verbose flag for debug printouts.'
    )

    running_mode = parser.add_mutually_exclusive_group()

    running_mode.add_argument(
        '-l', '--local', action='store_true',
        help='Override flag to run locally.'
    )
    running_mode.add_argument(
        '-b', '--batch', action='store_true',
        help='Override flag to run in batch.'
    )

    args = parser.parse_args(argv)

    return args

def main(argv=None):

    args = parse_command_line(argv)

    timestamp = time.strftime('%a_%b_%d_%Y_%H-%M-%S')

    if args.verbose:
        print 'List of Samples: {!s}\n'.format(args.samples)
        print 'Current Timestamp: {}\n'.format(timestamp)

    # the list of the config is taken from the path config
    configDir = args.tag + 'config'
    parser = myutils.BetterConfigParser()
    parser.read(os.path.join(configDir, 'paths.ini'))
    configs = [os.path.join(configDir, config) for config in parser.get('Configuration', 'List').split()]
    parser.read(configs)

    if args.verbose:
        print 'configs',configs
        print 'args.tagdir',args.tagdir

    if args.tagdir != '':
        tagDir = parser.get('Directories', 'tagDir')
        if args.verbose:
            print 'tagDir',tagDir

        DirStruct = {
            'tagDir': tagDir,
            'ftagdir': '%s/%s/' % (tagDir, args.tagdir),
            'logpath': '%s/%s/%s/' % (tagDir, args.tagdir, 'Logs'),
            'plotpath': '%s/%s/%s/' % (tagDir, args.tagdir, 'Plots'),
            'limitpath': '%s/%s/%s/' % (tagDir, args.tagdir, 'Limits'),
            'confpath': '%s/%s/%s/' % (tagDir, args.tagdir, 'config')
        }

        if args.verbose:
            print 'DirStruct', DirStruct

        for keys in ['tagDir', 'ftagdir', 'logpath', 'plotpath', 'limitpath', 'confpath']:
            try:
                os.stat(DirStruct[keys])
            except:
                os.mkdir(DirStruct[keys])

        pathfile = open('%sconfig/paths.ini' % args.tag)
        buffer = pathfile.readlines()
        pathfile.close()
        os.rename('%sconfig/paths.ini' % args.tag,'%sconfig/paths.ini.bkp' % args.tag)
        pathfile = open('%sconfig/paths.ini' % args.tag, 'w')
        for line in buffer:
            if line.startswith('plotpath'):
                line = 'plotpath = %s\n' % DirStruct['plotpath']
            elif line.startswith('logpath'):
                line = 'logpath = %s\n' % DirStruct['logpath']
            elif line.startswith('limits'):
                line = 'limits = %s\n' % DirStruct['limitpath']
            pathfile.write(line)
        pathfile.close()

        #copy config files
        for item in configs:
            shutil.copyfile(item, '%s/%s/%s' % (tagDir, args.tagdir, item.strip(args.tag)))

    # RETRIEVE RELEVANT VARIABLES FROM CONFIG FILES AND FROM COMMAND LINE OPTIONS
    logPath = parser.get('Directories', 'logpath')
    samplesinfo = parser.get('Directories', 'samplesinfo')
    whereToLaunch = parser.get('Configuration', 'whereToLaunch')
    run_locally = parser.getboolean('Configuration', 'run_locally')

    if args.local:
        print 'Overriding the "run_locally" configuration option with the local flag.\n'
        run_locally = True
    elif args.batch:
        print 'Overriding the "run_locally" configuration option with the batch flag.\n'
        run_locally = False

    print 'whereToLaunch', whereToLaunch
    print 'run_locally', run_locally

    # CREATE DIRECTORIES FOR PSI
    if 'PSI' in whereToLaunch:
      print 'Create the ouput folders PREPout, SYSout, MVAout if not existing'

      mkdir_list = [
          parser.get('Directories', 'PREPout').replace('root://t3dcachedb03.psi.ch:1094/', ''),
          parser.get('Directories', 'SYSout').replace('root://t3dcachedb03.psi.ch:1094/', ''),
          parser.get('Directories', 'MVAout').replace('root://t3dcachedb03.psi.ch:1094/', ''),
          parser.get('Directories', 'tmpSamples').replace('root://t3dcachedb03.psi.ch:1094/', ''),
      ]

      for mkdir_protocol in mkdir_list:
        if args.verbose:
            print 'checking',mkdir_protocol
        _output_folder = ''
        for _folder in mkdir_protocol.split('/'):
            _output_folder += '/' + _folder
            if not os.path.exists(_output_folder):
                command = 'srmmkdir srm://t3se01.psi.ch/' + _output_folder
                subprocess.check_call([command], shell = True)

    def dump_config(configs, output_file):
        """
        Dump all the configs in a output file
        Args:
            output_file: the file where the log will be dumped
            configs: list of files (string) to be dumped
        Returns:
            nothing
        """
        with open(output_file, 'w') as outf:
            for i in configs:
                try:
                    f = open(i, 'r')
                    outf.write(f.read())
                except:
                    print 'WARNING: Config' + i + ' not found. It will not be used.'

    def compile_macro(config, macro):
        """
        Creates the library from a macro using CINT compiling it in scratch to avoid
        problems with the linking in the working nodes.
        Args:
            config: configuration file where the macro path is specified
            macro: macro name to be compiled
        Returns:
            nothing
        """
        submitDir = os.getcwd()
        _macro = macro + '.h'
        library = parser.get(macro, 'library')
        libDir = os.path.dirname(library)
        os.chdir(libDir)
        if not os.path.exists(library):
            print 'INFO: Compiling ' + _macro
            scratchDir = '/scratch/%s/' % getpass.getuser()
            os.system("cp " + libDir + '/* /scratch/%s/' % getpass.getuser()) # OTHERWISE WILL NOT COMPILE SINCE INCLUDES OTHER FILES!!!
            os.chdir(scratchDir)
            print os.listdir(scratchDir)
            ROOT.gROOT.ProcessLine('.L %s+' % (scratchDir + _macro)) # CRASHES WHILE COMPILING THE SECOND ONE...
            shutil.copyfile('/scratch/%s/%s' % (getpass.getuser(), os.path.basename(library)), library)
            print 'INFO: macro', macro, 'compiled, exiting to avoid stupid ROOT crash, please resubmit!!!'
            sys.exit(1)
        os.chdir(submitDir)

    print '===============================\n'
    print 'Compiling the macros'
    print '===============================\n'
    # compile_macro(config,'BTagReshaping')
    compile_macro(config,'VHbbNameSpace')

    #check if the logPath exist. If not exit
    if not os.path.isdir(logPath):
        print '@ERROR : ' + logPath + ': dir not found.'
        print '@ERROR : Create it before submitting '
        print 'Exit'
        sys.exit(-1)

    # CREATE DICTIONARY TO BE USED AT JOB SUBMISSION TIME
    job_options = {
        'tag': args.tag,
        'logpath': logPath,
        'job': '',
        'task': args.task,
        'queue': 'all.q',
        'timestamp': timestamp,
        'bdt_params': '',
        'job_id': 'noid',
        'nprocesses': str(max(parser.getint('Configuration', 'nprocesses'), 1))
    }

    # STANDARD WORKFLOW SUBMISSION FUNCTION
    def submit(job, job_options, redirect_to_null=False):
        job_options['job'] = job
        global counter
        counter = 0
        counter += 1
        job_options['name'] = '%(job)s_%(tag)s%(task)s' % job_options
        if not run_locally:
            if whereToLaunch == 'lxplus':
                command = 'bsub -q 1nh -J {name} -o {logpath}/{timestamp}_{job}_{tag}_{task}.out runAll.sh {job} {tag} {task} {nprocesses} {job_id}'.format(**job_options)
            else:
                command = 'qsub -V -cwd -q %(queue)s -l h_vmem=6G -N %(name)s -j y -o %(logpath)s/%(timestamp)s_%(job)s_%(tag)s_%(task)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(tag)s ' %(job_options) + args.task + ' ' + job_options['nprocesses']+ ' ' + job_options['job_id'] + ' ' + job_options['bdt_params']
            print 'the command is ', command
            dump_config(configs, '%(logpath)s/%(timestamp)s_%(job)s_%(tag)s_%(task)s.config' % job_options)
            subprocess.check_call([command], shell=True)
        else:
            waiting_time_before_retry = 60
            number_symultaneous_process = 4
            counter = int(subprocess.check_output('ps aux | grep $USER | grep '+args.task +' | wc -l', shell=True))-1# add 1 to remove submithem count
            print 'counter command is', 'ps aux | grep $USER | grep '+args.task +' | wc -l'
            while counter > number_symultaneous_process:
                print 'counter is', counter
                print 'waiting', waiting_time_before_retry, 'seconds before to retry'
                os.system('sleep ' + str(waiting_time_before_retry))
                counter = int(subprocess.check_output('ps aux | grep $USER | grep '+args.task +' | wc -l', shell=True))

            command = 'sh runAll.sh %(job)s %(tag)s ' % (job_options) + args.task + ' ' + job_options['nprocesses']+ ' ' + job_options['job_id'] + ' ' + job_options['bdt_params']
            if redirect_to_null:
                command = command + ' 2>&1 > /dev/null &'
            else:
                command = command + ' 2>&1 > %(logpath)s/%(timestamp)s_%(job)s_%(tag)s_%(task)s.out' %(job_options) + ' &'
            print 'the command is ', command
            dump_config(configs, '%(logpath)s/%(timestamp)s_%(job)s_%(tag)s_%(task)s.config' % job_options)
            subprocess.check_call([command], shell=True)

    # SINGLE (i.e. FILE BY FILE) AND SPLITTED FILE WORKFLOW SUBMISSION FUNCTION
    def submitsinglefile(job, job_options, file, run_locally, counter_local):
        job_options['job'] = job
        global counter
        counter = 0
        counter += 1
        job_options['name'] = '%(job)s_%(tag)s%(task)s' % job_options
        if run_locally:
            command = 'sh runAll.sh %(job)s %(tag)s ' % (job_options) + args.task + ' ' + job_options['nprocesses']+ ' ' + job_options['job_id'] + ' ' + ('0' if not job_options['bdt_params'] else job_options['bdt_params'])
        elif whereToLaunch == 'lxplus':
            command = 'bsub -q 1nh -J {name} -o {logpath}/{timestamp}_{job}_{tag}_{task}.out runAll.sh {job} {tag} {task} {nprocesses} {job_id}'.format(**job_options)
        else:
            command = 'qsub -V -cwd -q %(queue)s -l h_vmem=6G -N %(name)s -j y -o %(logpath)s/%(timestamp)s_%(job)s_%(tag)s_%(task)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(tag)s ' %(job_options) + args.task + ' ' + job_options['nprocesses']+ ' ' + job_options['job_id'] + ' ' + ('0' if not job_options['bdt_params'] else job_options['bdt_params'])
            command = command.replace('.out', '_' + str(counter_local) + '.out')
        print 'the command is ', command
        print 'submitting', len(file.split(';')), 'files like', file.split(';')[0]
        command = command + ' "' + str(file)+ '"'
        dump_config(configs, '%(logpath)s/%(timestamp)s_%(job)s_%(tag)s_%(task)s.config' % (job_options))
        subprocess.check_call([command], shell=True)

    # MERGING FUNCTION FOR SINGLE (i.e. FILE BY FILE) AND SPLITTED FILE WORKFLOW TO BE COMPATIBLE WITH THE OLD WORKFLOW
    def mergesubmitsinglefile(job, job_options, run_locally):
        job_options['job'] = job
        global counter
        counter = 0
        counter += 1
        job_options['name'] = '%(job)s_%(tag)s%(task)s' % job_options
        if run_locally:
            command = 'sh runAll.sh %(job)s %(tag)s ' % (job_options) + args.task + ' ' + job_options['nprocesses']+ ' ' + job_options['job_id'] + ' ' + ('0' if not job_options['bdt_params'] else job_options['bdt_params'])
        elif whereToLaunch == 'lxplus':
            command = 'bsub -q 1nh -J {name} -o {logpath}/{timestamp}_{job}_{tag}_{task}.out runAll.sh {job} {tag} {task} {nprocesses} {job_id}'.format(**job_options)
        else:
            command = 'qsub -V -cwd -q %(queue)s -l h_vmem=6G -N %(name)s -j y -o %(logpath)s/%(timestamp)s_%(job)s_%(tag)s_%(task)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(tag)s ' %(job_options) + args.task + ' ' + job_options['nprocesses']+ ' ' + job_options['job_id'] + ' ' + ('0' if not job_options['bdt_params'] else job_options['bdt_params'])
        command = command + ' mergeall'
        print 'the command is ', command
        dump_config(configs, '%(logpath)s/%(timestamp)s_%(job)s_%(tag)s_%(task)s.config' % (job_options))
        subprocess.check_call([command], shell=True)

    # RETRIEVE FILELIST FOR THE TREECOPIER PSI AND SINGLE FILE SYS STEPS
    def getfilelist(job):
        samplefiles = parser.get('Directories', 'samplefiles')
        filelist = myutils.copytreePSI.filelist(samplefiles, job)
        return filelist

    if args.task == 'train':
        train_list = parser.get('MVALists', 'List_for_submitscript').split(',')
        print train_list
        for item in train_list:
            submit(item, job_options)


    if args.task == 'dc':
        DC_vars= parser.get('LimitGeneral', 'List').split(',')
        print DC_vars

    if args.task == 'plot':
        Plot_vars= parser.get('Plot_general', 'List').split(',')

    if not args.task == 'prep':
        path = parser.get('Directories', 'samplepath')
        info = myutils.ParseInfo(samplesinfo, path)

    if args.task == 'plot':
        job_options['queue'] = 'all.q'
        for item in Plot_vars:
            submit(item, job_options)


    if args.task == 'trainReg':
        job_options['queue'] = 'all.q'
        submit('trainReg', job_options)


    elif args.task == 'dc':
        job_options['queue'] = 'all.q'
        for item in DC_vars:
            # item here contains the dc name
            submit(item, job_options)


    elif args.task == 'prep':
        if not args.samples:
            path = parser.get('Directories', 'PREPin')
            info = myutils.ParseInfo(samplesinfo, path)
            for job in info:
                submit(job.name, job_options)
        else:
            for sample in args.samples:
                submit(sample, job_options)


    elif args.task in ['singleprep', 'singlesys', 'singleeval', 'mergesingleprep', 'mergesinglesys', 'mergesingleeval']:
        if not args.samples:
            if args.task == 'singleprep' or args.task == 'mergesingleprep':
                path = parser.get('Directories', 'PREPin')
            elif args.task == 'singlesys' or args.task == 'mergesinglesys':
                path = parser.get('Directories', 'SYSin')
            elif args.task == 'singleeval' or args.task == 'mergesingleeval':
                path = parser.get('Directories', 'MVAin')
            info = myutils.ParseInfo(samplesinfo, path)
            sample_list = []
            for job in info:
                sample_list.append(job.identifier)
            sample_list = set(sample_list)
        else:
            sample_list = set(args.samples)

        for sample in sample_list:
            if sample == '':
                continue
            if args.task == 'singleprep' or args.task == 'singlesys' or args.task == 'singleeval':
                files = getfilelist(sample)
                files_per_job = args.nsplit if args.nsplit > 0 else parser.getint('Configuration', 'files_per_job')
                files_split=[files[x:x+files_per_job] for x in xrange(0, len(files), files_per_job)]
                files_split = [';'.join(sublist) for sublist in files_split]
                counter_local = 0
                for files_sublist in files_split:
                    submitsinglefile(sample, job_options, files_sublist, run_locally, counter_local)
                    counter_local = counter_local + 1
            elif args.task == 'mergesingleprep' or args.task == 'mergesinglesys' or args.task == 'mergesingleeval':
                mergesubmitsinglefile(sample, job_options, run_locally)


    # ADD SYSTEMATIC UNCERTAINTIES AND ADDITIONAL HIGHER LEVEL VARIABLES TO THE TREES
    elif args.task == 'sys' or args.task == 'syseval':
        path = parser.get('Directories', 'SYSin')
        info = myutils.ParseInfo(samplesinfo, path)
        if not args.samples:
            for job in info:
                if job.subsample:
                    continue # avoid multiple submissions form subsamples
                # TO FIX FOR SPLITTED SAMPLE
                submit(job.name, job_options)
        else:
            for sample in args.samples:
                submit(sample, job_options)

    # EVALUATION OF EVENT BY EVENT BDT SCORE
    elif args.task == 'eval':
        job_options['queue'] = 'long.q'
        path = parser.get('Directories', 'MVAin')
        info = myutils.ParseInfo(samplesinfo, path)
        if not args.samples:
            for job in info:
                if job.subsample:
                    continue # avoid multiple submissions from subsamples
                if info.checkSplittedSampleName(job.identifier): # if multiple entries for one name  (splitted samples) use the identifier to submit
                    print 'INFO: Splitted samples: submit through identifier'
                    submit(job.identifier, job_options)
                else:
                    submit(job.name, job_options)
        else:
            for sample in args.samples:
                print sample
                submit(sample, job_options)

    # POSSIBILITY TO SPLIT SINGLE MERGED FILES IN SUBFILES
    # IN PRINCIPLE USEFUL BUT NOT USED ANYMORE AS THE LOGIC CHANGED (I.E. DON'T MERGE FILES)
    elif args.task == 'split':
        path = parser.get('Directories', 'SPLITin')
        job_options['job_id'] = args.nsplit if args.nsplit > 0 else 100000
        info = myutils.ParseInfo(samplesinfo, path)
        if not args.samples:
            for job in info:
                if job.subsample:
                    continue # avoid multiple submissions from subsamples
                submit(job.name, job_options)
        else:
            for sample in args.samples:
                submit(sample, job_options)


    # BDT optimisation
    elif args.task == 'mva_opt':
        total_number_of_steps = 1
        setting = ''
        for par in parser.get('Optimisation', 'parameters').split(','):
            scan_par = eval(parser.get('Optimisation', par))
            setting += par + '=' + str(scan_par[0]) + ':'
            if len(scan_par) > 1 and scan_par[2] != 0:
                total_number_of_steps += scan_par[2]
        #setting=setting[:-1] # eliminate last column at the end of the setting string
        #job_options['bdt_params']=setting
        job_options['bdt_params'] = 'main_par'
        job_options['job_id'] = parser.get('Optimisation', 'training')
        submit('OPT_main_set', job_options, False)
        main_setting = setting
        # Scanning all the parameters found in the training config in the Optimisation sector
        for par in parser.get('Optimisation', 'parameters').split(','):
            scan_par = eval(parser.get('Optimisation', par))
            if len(scan_par) > 1 and scan_par[2] != 0:
                for step in xrange(scan_par[2]):
                    value = scan_par[0] + (1+step)*(scan_par[1]-scan_par[0])/scan_par[2]
                    setting = re.sub(par + '.*?:', par + '=' + str(value) + ':', main_setting)
                    job_options['bdt_params'] = setting
                    submit('OPT_' + par + str(value), job_options, False)
                    # submit(parser.get('Optimisation','training'),job_options)

    elif args.task == 'mva_opt_eval':
        #
        #This step evaluate the BDT produced by mva_opt.
        #

        #Read the config
        job_options['queue'] = 'long.q'
        path = parser.get('Directories', 'MVAin')
        job_options['job_id'] = parser.get('Optimisation', 'training')
        factoryname = parser.get('factory', 'factoryname')
        MVAdir = parser.get('Directories', 'vhbbpath') + '/python/weights/'
        #Read weights from optimisaiton config, store the in a list (copied from mva_opt)
        total_number_of_steps = 1
        setting = ''
        for par in parser.get('Optimisation', 'parameters').split(','):
            scan_par = eval(parser.get('Optimisation', par))
            setting += par + '=' + str(scan_par[0]) + ':'
            if len(scan_par) > 1 and scan_par[2] != 0:
                total_number_of_steps += scan_par[2]
        job_options['bdt_params'] = setting
        job_options['job_id'] = parser.get('Optimisation','training')
        main_setting = setting
        config_weights_list = ['OPT_main_set']
        for par in parser.get('Optimisation', 'parameters').split(','):
            scan_par = eval(parser.get('Optimisation', par))
            if len(scan_par) > 1 and scan_par[2] != 0:
                for step in xrange(scan_par[2]):
                    value = scan_par[0] + (1+step)*(scan_par[1]-scan_par[0])/scan_par[2]
                    setting = re.sub(par + '.*?:', par + '=' + str(value) + ':', main_setting)
                    config_weights_list.append('OPT_' + par + str(value))
        #List all the weights produced from the optimisation, read from the weight directory. return weights_list
        weights = ''
        for cw in config_weights_list:
            for w in os.listdir(MVAdir):
                w = w.replace(factoryname + '_', '')
                w = w.replace('.root', '')
                if not w == cw:
                    continue
                weights += w + ','
        if weights[-1] == ',':
            weights = weights[:-1]#remove , at the end of the list
        #submit the jobs
        info = myutils.ParseInfo(samplesinfo, path)
        job_options['bdt_params'] = weights
        print 'The optimisation weights are', weights
        if not args.samples:
            for job in info:
                if job.subsample:
                    continue # avoid multiple submissions from subsamples
                if info.checkSplittedSampleName(job.identifier): # if multiple entries for one name  (splitted samples) use the identifier to submit
                    print '@INFO: Splitted samples: submit through identifier'
                    submit(job.identifier, job_options)
                else:
                    submit(job.name, job_options)
        else:
            for sample in args.samples:
                print sample
                submit(sample, job_options)

    #Work in progress...
    elif args.task == 'mva_opt_dc':
        total_number_of_steps = 1
        setting = ''
        for par in parser.get('Optimisation', 'parameters').split(','):
            scan_par = eval(parser.get('Optimisation', par))
            setting += par + '=' + str(scan_par[0]) + ':'
            if len(scan_par) > 1 and scan_par[2] != 0:
                total_number_of_steps += scan_par[2]
        print setting
        job_options['bdt_params'] = 'OPT_main_set'
        dc = parser.get('Optimisation', 'dc')
        #Still need to launch main
        submit(dc, job_options, False)
        main_setting = setting
        # Scanning all the parameters found in the training config in the Optimisation sector
        for par in parser.get('Optimisation','parameters').split(','):
            scan_par = eval(parser.get('Optimisation',par))
            print par
            if len(scan_par) > 1 and scan_par[2] != 0:
                for step in xrange(scan_par[2]):
                    value = scan_par[0] + (1+step)*(scan_par[1]-scan_par[0])/scan_par[2]
                    print value
                    job_options['bdt_params'] = 'OPT_' + par + str(value)
                    submit(dc, job_options, False)
                    print setting

    if args.philipp_love_progress_bars:
        os.system('qstat.py')

if __name__ == '__main__':

    status = main()
    sys.exit(status)

