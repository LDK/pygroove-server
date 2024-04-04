# This is a modification of https://gist.github.com/mixxorz/abb8a2f22adbdb6d387f
# Thank you mixxorz.
#
# Requires pydub (with ffmpeg) and Pillow
# 
import sys

from pydub import AudioSegment

class SampleData(object):
    def __init__(self, filename: str):
        self.filename = filename

        audio_file:AudioSegment = AudioSegment.from_file(
            self.filename, self.filename.split('.')[-1])

        self.audio_file = audio_file

    def length(self):
        return self.audio_file.duration_seconds * self.audio_file.frame_rate

if __name__ == '__main__':
    filename = sys.argv[1]

    data = SampleData(filename)
    data.length()