from methods import AllMethods, AllMatchMethod, LongestContinousMethod
from argparse import ArgumentParser
from PIL import Image
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


class Detector:
    jpg_folder = './jpgs'  # location of jpg images from video
    threshold = 0.35  # default threshold, can be passed as arg
    method = None  # detector method class
    debug = False


    def  __init__(self, threshold, method, level='info'):
        self.threshold = threshold

        if(level.lower() == 'debug'):
            self.debug = True

        if(method == 'all_match'):
            self.method = AllMatchMethod()
        elif(method == 'longest_common'):
            self.method = LongestContinousMethod()
        elif(method == 'all'):
            self.method = AllMethods()


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
        if category is "intro" and len(times) > 0:
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

        name, _ = os.path.splitext(path)
        name = os.path.join(self.jpg_folder, os.path.basename(name))
        if os.path.exists(name):
            shutil.rmtree(name)
        os.mkdir(name)

        input_file = path

        scene_file = os.path.join(self.jpg_folder, 'scenes')
        if category is "intro":
            scenes = "ffmpeg -i " + '"' + input_file + '"' + " -ss 0 -to " + \
                str(end_time) + ' -vf  "select=' + "'gt(scene," + str(th) + ")'," + \
                'showinfo" -vsync vfr "' + name + '/' + '"%04d.jpg>' + scene_file + ' 2>&1'
        elif category is "outro":
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
        name = os.path.join(self.jpg_folder, os.path.basename(name))
        hashlist, _ = self.get_hash_from_dir(name)
        if os.path.exists(name) and not self.debug:
            shutil.rmtree(name)

        return hashlist, scene_transitions


    def gen_timings_processed(self, videos_process):
        result = {}  # dict containing path: {intro,outro} information

        # Processing for Intros
        logging.info("Detecting intro for: %s" % os.path.basename(videos_process[0]))

        video_prev = videos_process[0]
        result[video_prev] = {}
        hash_prev, scene_prev = self.get_hash_video(
            videos_process[0], "intro")

        for i in range(1, len(videos_process)):
            logging.info("Detecting intro for: %s" % os.path.basename(videos_process[i]))
            result[videos_process[i]] = {}

            hash_cur, scene_cur = self.get_hash_video(
                videos_process[i], "intro")
            indices = self.method.get_common_intro(hash_prev, hash_cur)

            if(len(indices) > 0):
                try:
                    intro_start_prev = scene_prev[indices[0][0]]
                    intro_start_cur = scene_cur[indices[0][1]]

                    intro_end_prev = scene_prev[indices[-1][0] + 1]
                    intro_end_cur = scene_cur[indices[-1][1] + 1]

                except IndexError:
                    logging.error('Error finding scene index')

                if 'intro' not in result[video_prev]:
                    time_string = str(intro_start_prev) + " " + \
                        str(intro_end_prev) + " 4"  # cut in edl files
                    result[video_prev]['intro'] = time_string

                time_string = str(intro_start_cur) + " " + \
                        str(intro_end_cur) + " 4"  # cut in edl files
                result[videos_process[i]]['intro'] = time_string

            else:
                logging.info('No intro found for: %s' % os.path.basename(videos_process[i]))
                logging.debug('Comparison file: %s' % os.path.basename(video_prev))

            video_prev = videos_process[i]
            hash_prev = hash_cur
            scene_prev = scene_cur

        # Processing for Outros
        logging.info('Detecting outro for: %s' % os.path.basename(videos_process[0]))

        video_prev = videos_process[0]
        hash_prev, scene_prev = self.get_hash_video(
            videos_process[0], "outro")

        for i in range(1, len(videos_process)):
            logging.info('Detecting outro for: %s' % os.path.basename(videos_process[i]))
            hash_cur, scene_cur = self.get_hash_video(
                videos_process[i], "outro")
            indices = self.method.get_common_outro(hash_prev, hash_cur)

            if(len(indices) > 0):
                outro_start_prev = scene_prev[indices[0][0]]
                outro_start_cur = scene_cur[indices[0][1]]

                try:
                    outro_end_prev = scene_prev[indices[-1][0] + 1]
                except:
                    outro_end_prev = scene_prev[indices[-1][0]]

                try:
                    outro_end_cur = scene_cur[indices[-1][1] + 1]
                except:
                    outro_end_cur = scene_cur[indices[-1][1]]

                if 'outro' not in result[video_prev]:
                    time_string = str(outro_start_prev) + " " + \
                        str(outro_end_prev) + " 5"  # cut in edl files
                    result[video_prev]['outro'] = time_string

                time_string = str(outro_start_cur) + " " + \
                    str(outro_end_cur) + " 5"  # cut in edl files
                result[videos_process[i]]['outro'] = time_string
            else:
                logging.info('No outro found for: %s' % os.path.basename(videos_process[i]))
                logging.debug('Comparison file: %s' % os.path.basename(video_prev))

            video_prev = videos_process[i]
            hash_prev = hash_cur
            scene_prev = scene_cur

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
        if force is False:
            for file in videos:
                filename, _ = os.path.splitext(file)
                suffix = '.edl'
                if (filename + suffix) not in all_files:
                    videos_process.append(file)
        else:
            videos_process = copy.deepcopy(videos)

        if len(videos_process) == 0:
            logging.info("No videos to process.")
        elif len(videos_process) == 1 and len(videos) >= 2:
            vid = videos_process[0]
            videos.sort()  # basic ordering for videos by sorting based on season and episode
            try:
                comp_vid = videos[videos.index(vid) - 1]
            except:
                comp_vid = videos[videos.index(vid) + 1]
            timings = self.gen_timings_processed(
                [comp_vid, vid])
            self.create_edl(timings)
        else:
            videos_process.sort()  # basic ordering for videos by sorting based on season and episode
            timings = self.gen_timings_processed(
                videos_process)
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
        detector = Detector(self.args.threshold, self.args.method, self.args.log)
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
    logging.info('Max Workers: %d' % args.workers)

    detector = DetectorThreadManager(args)
    detector.start(args.path)

if __name__ == '__main__':
    main()
