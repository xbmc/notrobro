Prerequisites:
ffmpeg need to be installed beforehand globally and should be able to run via the command line interface. 


Arguments:
  -h, --help            (show this help message and exit)
  --path PATH, -p PATH  (TV show directory path) (mandatory argument)
  --threshold THRESHOLD, -t THRESHOLD
                        (Threshold for scene change detection(default=0.35))
  --method METHOD, -m METHOD
                        (Method used for timings generation (all_match (default) or longest_common))
  --force               (Process all videos in the directory (default=False))

Minimum Required Command:
	python3 detector.py --path /your/path/
	python3 detector.py -p /your/path/

Process all videos in the directory:
	python3 detector.py --path /your/path/ --force
	python3 detector.py -p /your/path/ --force

Change Threshold:
	python3 detector.py --path /your/path/ --threshold 0.5
	python3 detector.py -p /your/path/ -t 0.5

Change Method:
	python3 detector.py --path /your/path/ --method longest_common
 	python3 detector.py -p /your/path/ -m longest_common


(Tested on Ubuntu 16.04)
(Tested for Windows)
