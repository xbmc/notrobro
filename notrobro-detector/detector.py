from methods import AllMethods, AllMatchMethod, LongestContinousMethod
from argparse import ArgumentParser
from PIL import Image
import random
import signal
import sys
import os
import glob
import imagehash
import threading
import subprocess
import shutil
import copy
import time
import logging


class EDLReader:
    times = None

    def __init__(self, file):
        self.times = self._getTimings(file)

    def _getTimings(self, file):
        result = []
        if(os.path.exists(file)):
            with open(file, 'r') as f:
                result = f.readlines()

        return result

    def _hasAction(self, action_id):
        result = False

        i = 0
        while(i < len(self.times) and not result):
            # for each line check if the EDL action is the one we're looking for
            split_line = self.times[i].strip().split()

            if(int(split_line[2]) == action_id):
                result = True
            i = i + 1

        return result

    @property
    def hasIntro(self):
        return self._hasAction(4)

    @property
    def hasOutro(self):
        return self._hasAction(5)


class Detector:
    jpg_folder = './jpgs'  # location of jpg images from video
    threshold = 0.35  # default threshold, can be passed as arg
    method = None  # detector method class
    categories = None  # the categories to run detection on (intro, outro)
    debug = False


    def  __init__(self, threshold, method, categories=['intro','outro'], level='info'):
        self.threshold = threshold

        if(level.lower() == 'debug'):
            self.debug = True

        if(method == 'all_match'):
            self.method = AllMatchMethod()
        elif(method == 'longest_common'):
            self.method = LongestContinousMethod()
        elif(method == 'all'):
            self.method = AllMethods()

        self.categories = categories


    def get_hash(self, path):
        return imagehash.phash(Image.open(path))


    def get_hash_from_dir(self, path):
        images = os.listdir(path)
        images.sort()
        hashlist = []
        for img in images:
            hashlist.append(self.get_hash(os.path.join(path, img)))
        return hashlist, images


    def get_timings(self, out, category):
        to_find = "pts_time:"
        length = len(to_find)
        loc = -1
        times = []
        while True:
            loc = out.find(to_find, loc + 1)
            if loc == -1:
                break
            time = ""
            current = loc + length
            while out[current] != " ":
                time += out[current]
                current += 1
            times.append(time)
        if category == "intro" and len(times) > 0:
            del times[-1]
        return times


    def get_duration(self, out):
        result = 0
        to_find = "Duration: "
        length = len(to_find)
        loc = out.find(to_find, 0)
        if(loc != -1):
            duration = ""
            current = loc + length
            while out[current] != ",":
                duration += out[current]
                current += 1
            total = duration.split(":")
            result = float(total[0])*3600.0 + float(total[1])*60.0 + float(total[1])
        return result


    def get_scene_transitions(self, path, category):
        th = self.threshold
        end_time = 360  # in seconds (can be put in arguments as well)
        # in seconds from end of video (can be put in arguments as well)
        outro_end_time = -300

        # create jpg directory for video frames
        name, _ = os.path.splitext(path)
        name = os.path.join(self.jpg_folder, '%s_%s' % (os.path.basename(name), category))
        if not os.path.exists(name):
            os.mkdir(name)

        input_file = path

        scene_file = os.path.join(self.jpg_folder, 'scenes')
        if category == "intro":
            scenes = "ffmpeg -i " + '"' + input_file + '"' + " -ss 0 -to " + \
                str(end_time) + ' -vf  "select=' + "'gt(scene," + str(th) + ")'," + \
                'showinfo" -vsync vfr "' + name + '/' + '"%04d.jpg>' + scene_file + ' 2>&1'
        elif category == "outro":
            scenes = "ffmpeg -sseof " + str(outro_end_time) + " -i " + '"' + input_file + '"' + ' -vf  "select=' + \
                "'gt(scene," + str(th) + ")'," + 'showinfo" -vsync vfr "' + \
                   name + '/' + '"%04d.jpg>' + scene_file + ' 2>&1'

        subprocess.call(scenes, shell=True)

        file = open(scene_file, "r")
        out = file.read()
        file.close()
        times = self.get_timings(out, category)

        os.remove(scene_file)

        return times


    def get_hash_video(self, path, category):
        scene_transitions = self.get_scene_transitions(path, category)
        if category == "outro":
            duration_file = os.path.join(self.jpg_folder, "duration")
            duration = "ffmpeg -i " + '"' + path + '"' + ">" + duration_file + " 2>&1"
            subprocess.call(duration, shell=True)
            file = open(duration_file, "r")
            out = file.read()
            file.close()
            total_time = self.get_duration(out)
            os.remove(duration_file)
            outro_end_time = -300
            begin = total_time + outro_end_time
            for i in range(len(scene_transitions)):
                scene_transitions[i] = str(float(scene_transitions[i]) + begin)
        name, _ = os.path.splitext(path)
        name = os.path.join(self.jpg_folder, '%s_%s' % (os.path.basename(name), category))
        hashlist, _ = self.get_hash_from_dir(name)

        return hashlist, scene_transitions

    def make_timestring(self, timings, category):
        # EDL format is "start end action"
        actions = {'intro': 4, 'outro': 5}
        return "%s %s %d" % (str(timings[0]), str(timings[1]), actions[category])


    def compare_videos(self, video1, video2, category, video_list):
        logging.info('processing %s for %s, %d tries left' % (category, os.path.basename(video2), len(video_list)))
        result = {}
        first_hash, first_scene = self.get_hash_video(video1, category)
        second_hash, second_scene = self.get_hash_video(video2, category)

        if(category == 'intro'):
            indices = self.method.get_common_intro(first_hash, second_hash)
        else:
            indices = self.method.get_common_outro(first_hash, second_hash)

        if(len(indices) > 0):
            try:
                first_start = first_scene[indices[0][0]]
                second_start = second_scene[indices[0][1]]

                if(category == 'intro'):
                    first_end = first_scene[indices[-1][0] + 1]
                    second_end = second_scene[indices[-1][1] + 1]
                else:
                    first_end = first_scene[indices[-1][0]]
                    second_end = second_scene[indices[-1][1]]


                result['video1'] = {'file': video1, 'timings': (first_start, first_end)}
                result['video2'] = {'file': video2, 'timings': (second_start, second_end)}

            except IndexError:
                logging.error('error finding scene index')

        # if nothing was found attempt to try another video comparison
        if(len(result) == 0 and len(video_list) > 0):
            result = self.compare_videos(video_list.pop(), video2, category, video_list)

        return result

    def gen_timings_processed(self, videos_process, intro_found, outro_found):
        result = {}  # dict containing path: {intro,outro} information
        timings_found = {'intro': intro_found, 'outro': outro_found}  # list of videos that have succeeded in finding intros/outros, used for regressive comparisons

        # Processing for Intros
        video_prev = videos_process[0]
        result[video_prev] = {}

        for i in range(1, len(videos_process)):
            result[videos_process[i]] = {}

            # run same loop for each category (intro and outro by default)
            for category in self.categories:
                # find times, result dict is {'video1': {'file':'', 'timings':(), .....}
                times = self.compare_videos(video_prev, videos_process[i], category, copy.deepcopy(timings_found[category]))

                if(len(times) > 0):

                    # check that video1 exists, we want an EDL for it (precence in result), and we haven't found an EDL already
                    if 'video1' in times and times['video1']['file'] in result and category not in result[times['video1']['file']]:
                        result[times['video1']['file']][category] = self.make_timestring(times['video1']['timings'], category)

                    if(times['video1']['file'] not in timings_found[category]):
                        logging.debug('adding %s to found list for: %s' % (category, times['video1']['file']))
                        timings_found[category].append(times['video1']['file'])

                    if 'video2' in times:
                        result[videos_process[i]][category] = self.make_timestring(times['video2']['timings'], category)
                else:
                    logging.info('No %s found for: %s' % (category, os.path.basename(videos_process[i])))

            video_prev = videos_process[i]

        return result


    def create_edl(self, timings):
        for file in timings.keys():
            filename, _ = os.path.splitext(file)
            suffix = '.edl'
            edl_file = filename + suffix

            # only write the file if a timing exists for this video
            if('intro' in timings[file] or 'outro' in timings[file]):
                with open(edl_file, 'w') as f:
                    if 'intro' in timings[file]:
                        f.write(timings[file]['intro'] + "\n")
                    if 'outro' in timings[file]:
                        f.write(timings[file]['outro'] + "\n")

        logging.info('Timing files created.')


    def generate(self, path, force):
        # jpg folder should have unique path for this thread
        self.jpg_folder = './%d' % threading.current_thread().ident

        files = os.listdir(path)
        all_files = [os.path.join(path, i) for i in files]

        # get the video files
        videos = []
        for ext in ('*.mp4', '*.mkv', '*.avi', '*.mov', '*.wmv'):  # video formats - extendable
            videos.extend(glob.glob(os.path.join(path, ext)))

        # read in any manually excluded files
        exclude_list = []
        if(os.path.exists(os.path.join(path, 'edl_exclude.txt'))):
            logging.debug('Found exclude file in %s' % path)
            with open(os.path.join(path, 'edl_exclude.txt')) as f:
                exclude_list = f.readlines()
            exclude_list = list(map(lambda x: x.strip(), exclude_list))

        # if there is only 1 video in the directory
        if len(videos) == 1:
            logging.info("Add at least 1 more video of the TV show to the directory for processing.")

        if(not os.path.exists(self.jpg_folder)):
            os.mkdir(self.jpg_folder)

        # mark a file within the folder with the base path of this detector (for debug)
        with open(os.path.join(self.jpg_folder, 'path.txt'), 'w') as f:
            f.write(path)

        # get videos which don't have a skip timings file (currently edl) according to --force parameter
        videos_process = []
        intro_found = []
        outro_found = []
        if force is False:
            for file in videos:
                filename, _ = os.path.splitext(file)
                suffix = '.edl'
                if (filename + suffix) not in all_files:
                    if(os.path.basename(file) not in exclude_list):
                        videos_process.append(file)
                    else:
                        logging.info('skipping %s - in exclude list' % os.path.basename(file))
                else:
                    parser = EDLReader(filename + suffix)

                    if(parser.hasIntro):
                        logging.debug('Intro found for %s' % os.path.basename(file))
                        intro_found.append(file)

                    if(parser.hasOutro):
                        logging.debug('Outro found for %s' % os.path.basename(file))
                        outro_found.append(file)
        else:
            videos_process = copy.deepcopy(videos)

        if len(videos_process) == 1 and len(videos) > 1:
            # need at least 2 videos to start processing
            index = 0
            while(videos[index] != videos_process[0] and videos[index] not in exclude_list):
                index = random.randint(0,len(videos) - 1)
            videos_process.append(videos[index])

        if(len(videos_process) < 2):
            logging.info("No videos to process in %s" % path)
        else:
            videos_process.sort()  # basic ordering for videos by sorting based on season and episode
            timings = self.gen_timings_processed(
                videos_process, intro_found, outro_found)
            self.create_edl(timings)

        if(not self.debug):
            shutil.rmtree(self.jpg_folder)


class DetectorThreadManager():
    args = None  # args as passed from the CLI

    def __init__(self, args):
        self.args = args

    def start(self, base_dir):
        dirs_process = []

        # add base directory
        dirs_process.append(base_dir)

        # start the walk
        for root, dirs, files in os.walk(base_dir):
            for name in dirs:
                dirs_process.append(os.path.join(root, name))

        # process each dir as a thread, up to max threads at a time
        while(len(dirs_process) > 0):
            while(len(dirs_process) > 0 and len(threading.enumerate()) <= self.args.workers):
                t = threading.Thread(target=self.start_thread, args=(dirs_process.pop(),))
                t.daemon = True
                t.start()

            time.sleep(2)

        # wait for any final threads to finish
        for thread in threading.enumerate():
            if(not thread is threading.main_thread()):
                thread.join()

        logging.info('All directories processed')
        subprocess.call("stty sane", shell=True)

    def start_thread(self, dir):
        logging.info('Starting detector in: %s' % dir)
        detector = Detector(self.args.threshold, self.args.method, self.args.categories, self.args.log)
        detector.generate(dir, self.args.force)


def signal_handler(sig, frame):
    logging.info('You pressed Ctrl+C!')

    sys.exit(0)


def main():
    argparse = ArgumentParser()
    argparse.add_argument('--path', '-p', type=str,
                          help='TV show directory path', required=True)
    argparse.add_argument('--threshold', '-t', type=str,
                          help='Threshold for scene change detection (default=0.35)', default='0.35')
    argparse.add_argument('--method', '-m', type=str, choices=["all_match", "longest_common", "all"],
                          help='Method used for timings generation (all, all_match, or longest_common). "all" method will run every method until a match is found or no methods are left to try', default='all')
    argparse.add_argument('--categories', '-c', type=str, nargs='*', choices=['intro', 'outro'],
                           help='What categories to detect on each video, choices are intro and outro. Default detects both', default=['intro', 'outro'])
    argparse.add_argument('--workers', '-w', type=int,
                          help='How many directories to process (threads) at one time (default=4)', default=4)
    argparse.add_argument('--force', '-f', action='store_true',
                          help='Process all videos in the directory')
    argparse.add_argument('--log', '-l', type=str, choices=['info', 'debug'],
                          help='Run in debug mode, keeps temp files for analysis', default='info')
    args = argparse.parse_args()
    signal.signal(signal.SIGINT, signal_handler)

    # set the log level
    log_level = getattr(logging, args.log.upper())
    logging.basicConfig(format="%(levelname)s %(asctime)s %(threadName)s: %(message)s", level=log_level,
                        datefmt="%H:%M:%S")
    logging.debug('DEBUG logging enabled')

    if not os.path.exists(args.path):
        logging.info("TV show directory: " + args.path + " not found.")
        exit()
    else:
        if not os.path.isdir(args.path):
            logging.info("Path: " + args.path + " is not a directory.")
            exit()

    logging.info('Threshold: %s' % args.threshold)
    logging.info('Method: %s' % args.method)
    logging.info('Categories: %s', ', '.join(args.categories))
    logging.info('Max Workers: %d' % args.workers)

    detector = DetectorThreadManager(args)
    detector.start(args.path)

if __name__ == '__main__':
    main()
