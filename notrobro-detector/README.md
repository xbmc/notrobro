# Notrobro Detector

## Prerequisites:
ffmpeg need to be installed beforehand globally and should be able to run via the command line interface. 

Make sure you have any required python libraries by running: 

```

pip3 install -r requirements.txt

```

## Using the Detector:

The ```detector.py``` script is the main program that will run the detection algorithms on a single, or multiple directories. Best practice is to have all video files for at least one entire season in a directory. This will be compared against to find common video frames for intro/outro detection. Directories are traversed recursively from whatever the first directory (--path argument). 

Additionally a file ```edl_exclude.txt``` can be put in each directory with a list of files to exclude from the detector (unless using -f). This is useful for files you know don't have intros or outros to avoid repeat processing on future runs.

Argument | Description
--- | --- 
  --path PATH, -p PATH | TV show directory path (mandatory argument), can be a directory containing multiple shows in subdirectories
  -h, --help | show this help message and exit
  --threshold THRESHOLD, -t THRESHOLD | Threshold for scene change detection (default=0.35)
  --method METHOD, -m METHOD | Method used for timings generation. Options are __all__ (default), __all_match__ or __longest_common__. 
  --categories LIST, -c LIST | Categories to detect, can be multiple. Options are __intro__ and __outro__. Default is both. 
  --workers MAX, -w MAX | The total number of directories that can be processed at one time, each in its own thread (default=4)
  --log LEVEL, -l LEVEL | set the log level. Options are __info__(default) and __debug__. Debug mode will retain all generated scene files and jpg images for debugging purposes. 
  --force, -f | Process all videos in the directory, even if they contain EDL files or are in the exclusion list (default=False)

Minimum Required Command:
```shell
	python3 detector.py --path /your/path/
	python3 detector.py -p /your/path/
```

Process all videos in the directory, regardless of existing EDL file:
```shell
	python3 detector.py --path /your/path/ --force
	python3 detector.py -p /your/path/ --force
```

Change Threshold:
```shell
	python3 detector.py --path /your/path/ --threshold 0.5
	python3 detector.py -p /your/path/ -t 0.5
```

Change Method:
```shell
	python3 detector.py --path /your/path/ --method longest_common
        python3 detector.py -p /your/path/ -m longest_common
```

Run more workers:
```shell
        python3 detector.py --path /your/path --workers 5
        python3 detector.py -p /your/path -w 5
```
