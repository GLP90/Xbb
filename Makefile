all: interface/VHbbNameSpace_h.so interface/BTagCalibrationStandalone_cpp.so interface/Rochester2016_h.so interface/TKinFitter_cc.so 

interface/VHbbNameSpace_h.so: interface/VHbbNameSpace.h
	 cd interface && root -b -l -q ../init.cc && cd ..	 

interface/BTagCalibrationStandalone_cpp.so: interface/BTagCalibrationStandalone.cpp
	 cd interface && root -b -l -q ../init.cc && cd ..

interface/Rochester2016_h.so: interface/Rochester2016.h
	cd interface && root -b -l -q ../init_rochester.cc && cd ..

interface/TKinFitter_cc.so:
	ROOT_INCLUDE_PATH=$$CMSSW_BASE/Xbb/:$$ROOT_INCLUDE_PATH
	cd interface && root -b -l -q ../init_kinfitter.cc && cd ..

clean:
	 rm interface/VHbbNameSpace_h.so
	 rm interface/VHbbNameSpace_h.d
	 rm interface/VHbbNameSpace_h_ACLiC_dict_rdict.pcm
	 rm interface/BTagCalibrationStandalone_cpp.so
	 rm interface/BTagCalibrationStandalone_cpp.d
	 rm interface/BTagCalibrationStandalone_cpp_ACLiC_dict_rdict.pcm
	 rm interface/Rochester2016_h.so
	 rm interface/Rochester2016_h.d
	 rm interface/Rochester2016_h_ACLiC_dict_rdict.pcm
