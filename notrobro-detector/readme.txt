Arguments:
  -h, --help            (show this help message and exit)
  --path PATH, -p PATH  (TV show directory path) (mandatory argument)
  --threshold THRESHOLD, -t THRESHOLD
                        (Threshold for scene change detection(default=0.35))
  --method METHOD, -m METHOD
                        (Method used for timings generation (all_match (default) or longest_common))
  --force               (Process all videos in the directory (default=False))

Minimum Required Command:
	python3 hash_run.py --path /your/path/
	python3 hash_run.py -p /your/path/

Process all videos in the directory:
	python3 hash_run.py --path /your/path/ --force
	python3 hash_run.py -p /your/path/ --force

Change Threshold:
	python3 hash_run.py --path /your/path/ --threshold 0.5
	python3 hash_run.py -p /your/path/ -t 0.5

Change Method:
	python3 hash_run.py --path /your/path/ --method longest_common
 	python3 hash_run.py -p /your/path/ -m longest_common


(Tested on Ubuntu 16.04)
(Testing for Windows required)
