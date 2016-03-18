% Usage
python powerModel.py 

% For options
python powerModel.py --help

% Example parallel run
python -c "for q in range(50,60): print q/100.0" | parallel python powerModel.py -r 0.1 -q {}
