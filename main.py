# coding: utf-8
import argparse
import contextlib
import glob
import os
import shutil
import subprocess
import sys
import wave

import cv2
from pydub import AudioSegment
from tqdm import tqdm


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input', type=str, help='input folder path')
    parser.add_argument('-f','--framerate', type=int, default=46000, help='sound frame rate')
    parser.add_argument('-s','--speed', type=float, default=1.0, help='sound speed')
    args = parser.parse_args()
    return args

def get_NoteList(fpath):
    f = open(fpath)
    text = f.read()
    f.close()
    text = text.split('\n')
    note_list = []
    note = []
    for line in text:
        if line==':newpage':
            note_list += [note]
            note = []
        else:
            note += [line]
    return note_list

def make_Sound(args, text, fname):
    if line[0]==':': # silent
        sound_len = float(line[1:]) * 1000
        sound = AudioSegment.silent(duration=sound_len, frame_rate=args.framerate)
        sound.export(fname, format="wav")
    else: # talk
        open_jtalk = ['open_jtalk']
        mech = ['-x', '/usr/local/Cellar/open-jtalk/1.11/dic']
        htsvoice = ['-m', '/usr/local/Cellar/open-jtalk/1.11/voice/mei/mei_normal.htsvoice']
        speed = ['-r', str(args.speed)]
        sampling = ['-s', str(args.framerate)]
        outwav = ['-ow', fname]
        cmd = open_jtalk + mech + htsvoice + speed + sampling + outwav
        c = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        c.stdin.write(text.encode('utf-8'))
        c.stdin.close()
        c.wait()

def get_SoundLen(fname):
    with contextlib.closing(wave.open(fname,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return duration

def join_Sound(i, fname):
    sound_path_fname = './sound/tmp{:03}/sound_path.txt'.format(i)
    sound_list = sorted(glob.glob(os.path.join('./sound/tmp{:03}'.format(i), '*.wav')))
    sound_path = ''
    for line in sound_list:
        sound_path += 'file ' + os.path.split(line)[-1] + '\n'
    with open(sound_path_fname, mode='w') as f:
        f.write(sound_path)
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', sound_path_fname, '-loglevel', 'quiet', '-c', 'copy', fname]
    c = subprocess.call(cmd)

def adjust_Sound(fname, add_len=None):
    sound_len = get_SoundLen(fname)
    sound = AudioSegment.from_file(fname)
    add_len = int(sound_len+1) * 1000
    silent = AudioSegment.silent(duration=add_len)
    result = silent.overlay(sound, position=0)
    result.export(fname, format="wav")

def make_SilentVideo(slide, sound_len, fname):
    img = cv2.imread(slide)
    h, w = img.shape[:2]
    fourcc = cv2.VideoWriter_fourcc('m','p','4', 'v')
    video  = cv2.VideoWriter(fname, fourcc, 20.0, (w,h))
    framecount = sound_len * 20
    for _ in range(int(framecount)):
        video.write(img)
    video.release()

def join_SilentVideo_Sound(silent_video, sound, fname):
    cmd = ['ffmpeg', '-y', '-i', silent_video, '-i', sound, '-loglevel', 'quiet', './video/{:03}.mp4'.format(fname)]
    c = subprocess.call(cmd)

def join_Video():
    video_path_fname = './video/video_path.txt'
    video_list = sorted(glob.glob(os.path.join('./video', '*.mp4')))
    video_path = ''
    for line in video_list:
        video_path += 'file ' + os.path.split(line)[-1] + '\n'
    with open(video_path_fname, mode='w') as f:
        f.write(video_path)
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', video_path_fname, '-loglevel', 'quiet', '-c', 'copy', 'out.mp4']
    c = subprocess.call(cmd)


if __name__ == '__main__':
    args = get_args()

    os.makedirs('./sound', exist_ok=True)
    os.makedirs('./silent_video', exist_ok=True)
    os.makedirs('./video', exist_ok=True)

    note_list = get_NoteList(os.path.join(args.input, 'text.txt'))
    slide_path = sorted(glob.glob(os.path.join(args.input, '*.jpeg')))
    note_num, slide_num = len(note_list), len(slide_path)
    if note_num!=slide_num: 
        print('Cannot run')
        sys.exit()

    for i in tqdm(range(note_num)):
        sound_fname = './sound/{:03}.wav'.format(i)
        silent_video_fname = './silent_video/{:03}.mp4'.format(i)

        # make sound
        for j, line in enumerate(note_list[i]):
            os.makedirs('./sound/tmp{:03}'.format(i), exist_ok=True)
            tmp_fname = './sound/tmp{:03}/{:03}.wav'.format(i,j)
            make_Sound(args, line, tmp_fname)
        join_Sound(i, sound_fname)
        adjust_Sound(sound_fname)

        # make silentvideo
        sound_len = get_SoundLen(sound_fname)
        make_SilentVideo(slide_path[i], sound_len, silent_video_fname)

        # make video
        join_SilentVideo_Sound(silent_video_fname, sound_fname, i)

    join_Video()

    # delete tmp folders
    shutil.rmtree("sound")
    shutil.rmtree("silent_video")
    shutil.rmtree("video")
