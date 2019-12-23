from argparse import ArgumentParser
import signal
import sys
import os
import glob
import imagehash
from PIL import Image
import subprocess
import shutil
import copy


class Detector:

  def get_hash(path):
      return imagehash.phash(Image.open(path))


  def get_hash_from_dir(path):
      images = os.listdir(path)
      images.sort()
      hashlist = []
      for img in images:
          hashlist.append(self.get_hash(os.path.join(path, img)))
      return hashlist, images


  def get_timings(out, category):
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
      if category is "intro":
          del times[-1]
      return times


  def get_duration(out):
      to_find = "Duration: "
      length = len(to_find)
      loc = out.find(to_find, 0)
      duration = ""
      current = loc + length
      while out[current] != ",":
          duration += out[current]
          current += 1
      total = duration.split(":")
      to_sec = float(total[0])*3600.0 + float(total[1])*60.0 + float(total[1])
      return to_sec


  def get_scene_transitions(path, threshold, category):
      th = threshold
      end_time = 360  # in seconds (can be put in arguments as well)
      # in seconds from end of video (can be put in arguments as well)
      outro_end_time = -300

      name, _ = os.path.splitext(path)

      if os.path.exists(name):
          shutil.rmtree(name)
      os.mkdir(name)

      input_file = path

      if category is "intro":
          scenes = "ffmpeg -i " + '"' + input_file + '"' + " -ss 0 -to " + \
              str(end_time) + ' -vf  "select=' + "'gt(scene," + str(th) + ")'," + \
              'showinfo" -vsync vfr "' + name + '/' + '"%04d.jpg>scenes 2>&1'
      elif category is "outro":
          scenes = "ffmpeg -sseof " + str(outro_end_time) + " -i " + '"' + input_file + '"' + ' -vf  "select=' + \
              "'gt(scene," + str(th) + ")'," + 'showinfo" -vsync vfr "' + \
                 name + '/' + '"%04d.jpg>scenes 2>&1'

      subprocess.call(scenes, shell=True)

      file = open("scenes", "r")
      out = file.read()
      file.close()
      times = get_timings(out, category)
      os.remove("./scenes")

      return times


  def get_hash_video(path, threshold, category):
      scene_transitions = self.get_scene_transitions(path, threshold, category)
      if category == "outro":
          duration = "ffmpeg -i " + '"' + path + '"' + ">duration 2>&1"
          subprocess.call(duration, shell=True)
          file = open("duration", "r")
          out = file.read()
          file.close()
          total_time = get_duration(out)
          os.remove("./duration")
          outro_end_time = -300
          begin = total_time + outro_end_time
          for i in range(len(scene_transitions)):
              scene_transitions[i] = str(float(scene_transitions[i]) + begin)
      name, _ = os.path.splitext(path)
      hashlist, _ = self.get_hash_from_dir(name)
      if os.path.exists(name):
          shutil.rmtree(name)
      return hashlist, scene_transitions

  # Methods

  # (1) All common matches


  def common_elements(list1, list2):
      common = []
      for i, element in enumerate(list1):
          try:
              ind = list2.index(element)
              common.append((i, ind))
          except:
              pass
      return common

  # small modification for outros


  def common_elements_outro(list1, list2):
      common = []
      for i, element1 in enumerate(list1):
          for j, element2 in enumerate(list2):
              if (element1-element2) <= 5:
                  if len(common) != 0 and common[-1][1] < j:
                      common.append((i, j))
                      break
                  elif len(common) == 0:
                      common.append((i, j))
                      break
      return common

  # (2) Longest continuos match


  def longest_common_subarray(l1, l2):
      subarray = []
      indices = []
      len1, len2 = len(l1), len(l2)
      for i in range(len1):
          for j in range(len2):
              temp = 0
              cur_array = []
              cur_indices = []
              # hamming distance
              while ((i+temp < len1) and (j+temp < len2) and (l1[i+temp]-l2[j+temp]) <= 30):
                  cur_array.append(l2[j+temp])
                  cur_indices.append((i+temp, j+temp))
                  temp += 1
              if (len(cur_array) > len(subarray)):
                  subarray = cur_array
                  indices = cur_indices
      # return subarray, indices
      return indices


  def gen_timings_processed(videos_process, threshold, method):
      intro_times = []
      outro_times = []

      # Processing for Intros
      hash_prev, scene_prev = self.get_hash_video(
          videos_process[0], threshold, "intro")

      print("Finding Intros")
      print("\t%s" % videos_process[0])
      for i in range(1, len(videos_process)):
          hash_cur, scene_cur = self.get_hash_video(
              videos_process[i], threshold, "intro")
          if method == "all_match":
              indices = self.common_elements(hash_prev, hash_cur)

              intro_start_prev = scene_prev[indices[0][0]]
              intro_start_cur = scene_cur[indices[0][1]]

              intro_end_prev = scene_prev[indices[-1][0] + 1]
              intro_end_cur = scene_cur[indices[-1][1] + 1]

              if len(intro_times) == 0:
                  time_string = str(intro_start_prev) + " " + \
                      str(intro_end_prev) + " 4"  # cut in edl files
                  intro_times.append(time_string)

              time_string = str(intro_start_cur) + " " + \
                  str(intro_end_cur) + " 4"  # cut in edl files
              intro_times.append(time_string)
          elif method == "longest_common":
              indices = self.longest_common_subarray(hash_prev, hash_cur)

              intro_start_prev = scene_prev[indices[0][0]]
              intro_start_cur = scene_cur[indices[0][1]]

              intro_end_prev = scene_prev[indices[-1][0] + 1]
              intro_end_cur = scene_cur[indices[-1][1] + 1]

              if len(intro_times) == 0:
                  time_string = str(intro_start_prev) + " " + \
                      str(intro_end_prev) + " 4"  # cut in edl files
                  intro_times.append(time_string)

              time_string = str(intro_start_cur) + " " + \
                  str(intro_end_cur) + " 4"  # cut in edl files
              intro_times.append(time_string)

          hash_prev = hash_cur
          scene_prev = scene_cur

          print("\t%s" % videos_process[0])

      # Processing for Outros
      hash_prev, scene_prev = self.get_hash_video(
          videos_process[0], threshold, "outro")
      print('Finding Outros')
      print('\t%s' % videos_process[0])

      for i in range(1, len(videos_process)):
          hash_cur, scene_cur = self.get_hash_video(
              videos_process[i], threshold, "outro")
          indices = self.common_elements_outro(hash_prev, hash_cur)
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

          if len(outro_times) == 0:
              time_string = str(outro_start_prev) + " " + \
                  str(outro_end_prev) + " 5"  # cut in edl files
              outro_times.append(time_string)

          time_string = str(outro_start_cur) + " " + \
              str(outro_end_cur) + " 5"  # cut in edl files
          outro_times.append(time_string)

          hash_prev = hash_cur
          scene_prev = scene_cur

          print('\t%s' % videos_process[i])

      return intro_times, outro_times


  def create_edl(videos, intro_timings, outro_timings):
      for i, file in enumerate(videos):
          filename, _ = os.path.splitext(file)
          suffix = '.edl'
          edl_file = filename + suffix
          with open(edl_file, 'w') as f:
              if i <= len(intro_timings) - 1:
                  f.write(intro_timings[i] + "\n")
              if i <= len(outro_timings) - 1:
                  f.write(outro_timings[i] + "\n")


  def generate(path, threshold, method, force):
      files = os.listdir(path)
      all_files = [os.path.join(path, i) for i in files]

      # get the video files
      videos = []
      for ext in ('*.mp4', '*.mkv', '*.avi', '*.mov', '*.wmv'):  # video formats - extendable
          videos.extend(glob.glob(os.path.join(path, ext)))

      # if there is only 1 video in the directory
      if len(videos) == 1:
          print("Add atleast 1 more video of the TV show to the directory for processing.")
          exit()

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
          print("No videos to process.")
          exit()
      elif len(videos_process) == 1:
          vid = videos_process[0]
          videos.sort()  # basic ordering for videos by sorting based on season and episode
          try:
              comp_vid = videos[videos.index(vid) - 1]
          except:
              comp_vid = videos[videos.index(vid) + 1]
          intro_times, outro_times = self.gen_timings_processed(
              [comp_vid, vid], threshold, method)
          self.create_edl([vid], [intro_times[1]], [outro_times[1]])
      else:
          videos_process.sort()  # basic ordering for videos by sorting based on season and episode
          intro_times, outro_times = self.gen_timings_processed(
              videos_process, threshold, method)
          self.create_edl(videos_process, intro_times, outro_times)

      print("Timing files created.")


def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)


def main():
    argparse = ArgumentParser()
    argparse.add_argument('--path', '-p', type=str,
                          help='TV show directory path')
    argparse.add_argument('--threshold', '-t', type=str,
                          help='Threshold for scene change detection(default=0.35)', default='0.35')
    argparse.add_argument('--method', '-m', type=str,
                          help='Method used for timings generation (all_match or longest_common)', default='all_match')
    argparse.add_argument('--force', '-f', action='store_true',
                          help='Process all videos in the directory')
    args = argparse.parse_args()
    signal.signal(signal.SIGINT, signal_handler)

    if args.path is None:
        print("Enter a directory path.")
        exit()
    else:
        if not os.path.exists(args.path):
            print("TV show directory: " + args.path + " not found.")
            exit()
        else:
            if not os.path.isdir(args.path):
                print("Path: " + args.path + " is not a directory.")
                exit()

    if args.method != "all_match" and args.method != "longest_common":
        print("Enter correct method: (1) all_match (2) longest_common")
        exit()

    detector = Detector()
    detector.generate(args.path, args.threshold, args.method, args.force)


if __name__ == '__main__':
    main()
