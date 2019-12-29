# Notrobro Detector

## Prerequisites:
ffmpeg need to be installed beforehand globally and should be able to run via the command line interface. 

Make sure you have any required python libraries by running: 

```

pip3 -r requirements.txt

```

## Detector arguments:
Argument | Description
--- | --- 
  --path PATH, -p PATH | TV show directory path (mandatory argument)
  -h, --help | show this help message and exit
  --threshold THRESHOLD, -t THRESHOLD | Threshold for scene change detection(default=0.35)
  --method METHOD, -m METHOD | Method used for timings generation (all (default), all_match or longest_common)
  --force, -f | Process all videos in the directory (default=False)

Minimum Required Command:
```shell
	python3 detector.py --path /your/path/
	python3 detector.py -p /your/path/
```

Process all videos in the directory:
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
