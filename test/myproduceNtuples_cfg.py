import FWCore.ParameterSet.Config as cms

from FWCore.ParameterSet.VarParsing import VarParsing
from Configuration.StandardSequences.Eras import eras

options = VarParsing ('python')

#$$
#options.register('pileup', 200,
#                 VarParsing.multiplicity.singleton,
#                 VarParsing.varType.int,
#                 "Specify the pileup in the sample (used for choosing B tag MVA thresholds)"
#)
#$$

options.register('debug', False,
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.bool,
                 "Fro Debug purposes"
)

options.register('rerunBtag', True,
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.bool,
                 "Rerun the B tagging algorithms using new training"
)


options.register('GlobalTag', '106X_upgrade2023_realistic_v2',
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.string,
                 "Specify the global tag for the release "
)


options.register('Analyzr', 'Validator',
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.string,
                 "Specify which ntuplzer you want to run "
)

options.parseArguments()

process = cms.Process("MyAna", eras.Phase2)

# Geometry, GT, and other standard sequences
#$$ process.load('Configuration.Geometry.GeometryExtended2023D17Reco_cff')
process.load('Configuration.Geometry.GeometryExtended2023D41Reco_cff')
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load('Configuration.StandardSequences.Services_cff')
process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('Configuration.EventContent.EventContent_cff')
process.load('Configuration.StandardSequences.MagneticField_AutoFromDBCurrent_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff')
process.load("TrackingTools/TransientTrack/TransientTrackBuilder_cfi")
from Configuration.AlCa.GlobalTag_condDBv2 import GlobalTag
#process.GlobalTag = GlobalTag(process.GlobalTag, '103X_upgrade2023_realistic_v2', '')
process.GlobalTag = GlobalTag(process.GlobalTag, options.GlobalTag, '')

# Log settings
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 100
process.MessageLogger.cerr.threshold = 'INFO'
process.MessageLogger.categories.append('MyAna')
process.MessageLogger.cerr.INFO = cms.untracked.PSet(
        limit = cms.untracked.int32(0)
)


# Input

process.options   = cms.untracked.PSet(
    wantSummary = cms.untracked.bool(True),
    allowUnscheduled = cms.untracked.bool(True)
)

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(options.maxEvents) ) 

#$$
options.inputFiles = '/store/relval/CMSSW_10_6_0/RelValTTbar_14TeV/MINIAODSIM/106X_upgrade2023_realistic_v2_2023D41noPU-v1/10000/63866134-439C-FF4F-B4DF-7398A8787500.root'
#$$
#options.inputFiles =  '/store/relval/CMSSW_10_6_0/RelValElectronGunPt2To100/MINIAODSIM/PU25ns_106X_upgrade2023_realistic_v2_2023D41PU200-v1/10000/296F40A8-0271-2F47-A3FD-F2251046CAF6.root'
# '/store/relval/CMSSW_10_6_0_pre4/RelValTTbar_14TeV/MINIAODSIM/106X_upgrade2023_realistic_v2_2023D41noPU-v1/10000/EB281B96-007A-3344-A3E9-929D08BDC289.root'
options.secondaryInputFiles = ''

process.source = cms.Source("PoolSource",
                            fileNames = cms.untracked.vstring(
                                options.inputFiles 
        ),
                            
)

process.source.inputCommands = cms.untracked.vstring("keep *")

# HGCAL EGamma ID
process.load("RecoEgamma.Phase2InterimID.phase2EgammaPAT_cff")
# analysis
moduleName = options.Analyzr  
process.myana = cms.EDAnalyzer(moduleName)
process.load("TreeMaker.Ntuplzr."+moduleName+"_cfi")

process.myana.debug = options.debug

#$$
postfix='WithNewTraining'
patJetSource = 'selectedUpdatedPatJets'+postfix
#$$
from PhysicsTools.PatAlgos.tools.jetTools import updateJetCollection
# The updateJetCollection function uncorrect the jets from MiniAOD and 
# then recorrect them using the curren set of JEC in the event setup, recalculates
# btag discriminators from new training
# And the new name of the updated jet collection becomes selectedUpdatedPatJets+postfix
if options.rerunBtag:
    updateJetCollection(
	process,
	jetSource      = cms.InputTag('slimmedJetsPuppi'),
	pvSource       = cms.InputTag('offlineSlimmedPrimaryVertices'),
	svSource       = cms.InputTag('slimmedSecondaryVertices'),
	pfCandidates	= cms.InputTag('packedPFCandidates'),
	jetCorrections = ('AK4PFPuppi', cms.vstring(['L1FastJet', 'L2Relative', 'L3Absolute']), 'None'),
	btagDiscriminators = [
	    'pfDeepCSVJetTags:probb', 
	    'pfDeepCSVJetTags:probbb',
	    'pfDeepFlavourJetTags:probb',
	    'pfDeepFlavourJetTags:probbb',
	    'pfDeepFlavourJetTags:problepb'
	],
	postfix = postfix
    )
    process.myana.jets = cms.InputTag(patJetSource)

for key in options._register.keys():
    print "{:<20} : {}".format(key, getattr(options, key))


process.TFileService = cms.Service("TFileService",
                                   fileName = cms.string(options.outputFile)
                                   )

#$$
#Trick to make it work with rerunBtag
process.tsk = cms.Task()
for mod in process.producers_().itervalues():
    process.tsk.add(mod)
for mod in process.filters_().itervalues():
    process.tsk.add(mod)
#$$

# run

#$$
# process.p = cms.Path(process.phase2Egamma*process.myana)
process.p = cms.Path(process.phase2Egamma*process.myana, process.tsk)
#$$

#open('ntupleFileDump.py','w').write(process.dumpPython())
