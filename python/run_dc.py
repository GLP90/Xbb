#!/usr/bin/env python
from __future__ import print_function
import sys, ROOT, warnings
ROOT.gROOT.SetBatch(True)
#suppres the EvalInstace conversion warning bug
warnings.filterwarnings( action='ignore', category=RuntimeWarning, message='creating converter.*' )
from optparse import OptionParser
from myutils.Datacard import Datacard

# ------------------------------------------------------------------------------
# script to produce datacards from cached tree
# recommended to run it for one sample identifier per job
# ------------------------------------------------------------------------------
class RunDatacards(object):

    def __init__(self, config, region, useSampleIdentifiers=None, verbose=False, forceRedo=True):
        self.verbose = verbose
        self.forceRedo = forceRedo
        self.config = config
        self.region = region
        self.useSampleIdentifiers = useSampleIdentifiers
        self.dcMaker = Datacard(config=self.config, region=region)

    def run(self):
        if self.dcMaker:
            if not self.dcMaker.splitFilesExist(useSampleIdentifier=self.useSampleIdentifiers) or self.forceRedo:
                self.dcMaker.run(useSampleIdentifiers=self.useSampleIdentifiers)
            else:
                print ("nothing to do.")
        else:
            print ("\x1b[31mERROR: could not produce datacards\x1b[0m")

if __name__ == "__main__":
    # read arguments
    argv = sys.argv
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                              help="Verbose mode.")
    parser.add_option("-C", "--config", dest="config", default=[], action="append",
                          help="configuration file")
    parser.add_option("-t", "--regions", dest="regions", default='',
                          help="cut regions identifier")
    parser.add_option("-S","--sampleIdentifier", dest="sampleIdentifier", default='',
                          help="sample identifier (no subsample!)")
    parser.add_option("-f", "--force", action="store_true", dest="force", default=False,
                          help="force overwriting of already existing datacards")
    (opts, args) = parser.parse_args(argv)
    if opts.config == "":
            opts.config = "config"

    # Import after configure to get help message
    from myutils import BetterConfigParser

    # load config
    config = BetterConfigParser()
    config.read(opts.config)

    # if no region is given in argument, run it for all of them
    regionsListString = opts.regions if len(opts.regions.strip())>0 else config.get('LimitGeneral', 'List')
    regions = [x.strip() for x in regionsListString.split(',') if len(x.strip()) > 0]
    useSampleIdentifiers = opts.sampleIdentifier.split(',') if len(opts.sampleIdentifier) > 0 else None
    print("regions:", regions)
    for region in regions:
        print("init...")
        runDC = RunDatacards(config=config, region=region, useSampleIdentifiers=useSampleIdentifiers, forceRedo=opts.force)
        print("run...")
        runDC.run()
