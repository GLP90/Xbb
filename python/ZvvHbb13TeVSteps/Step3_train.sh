bash runAll.sh ZvvBDT ZvvHbb13TeV train         >& log/logTrainZH &
bash runAll.sh ZvvBDTTight ZvvHbb13TeV train    >& log/logTrainZHTight &
bash runAll.sh ZvvBDTNoMjj ZvvHbb13TeV train    >& log/logTrainZHNoMjj &

bash runAll.sh ZvvBDTOnlyPositiveWeights ZvvHbb13TeV train          >& log/logTrainZHOnlyPositiveWeights &
bash runAll.sh ZvvBDTNoMjjOnlyPositiveWeights ZvvHbb13TeV train     >& log/logTrainZHNoMjjOnlyPositiveWeights &


bash runAll.sh ZvvBDTHighPt ZvvHbb13TeV train       >& log/logTrainZHTightHighPt &
bash runAll.sh ZvvBDTLowPt ZvvHbb13TeV train        >& log/logTrainZHTightLowPt &
bash runAll.sh ZvvBDTTightHighPt ZvvHbb13TeV train  >& log/logTrainZHHighPt &
bash runAll.sh ZvvBDTTightLowPt ZvvHbb13TeV train   >& log/logTrainZHLowPt &

