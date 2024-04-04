# This is a modification of https://gist.github.com/mixxorz/abb8a2f22adbdb6d387f
# Thank you mixxorz.
#
# Requires pydub (with ffmpeg) and Pillow
# 
import io
import sys

from pydub import AudioSegment
from pydub.silence import detect_leading_silence
from PIL import Image, ImageDraw
import soundfile as sf

import librosa

from renderer.groove import librosaToPydub
from renderer.groove import chop

class SampleProcess(object):
    def __init__(self, filename: str, options: dict = None):
        self.filename = filename

        audio_file:AudioSegment = AudioSegment.from_file(
            self.filename, self.filename.split('.')[-1])

        trim_leading_silence = lambda x: x[detect_leading_silence(x) :]
        trim_trailing_silence = lambda x: trim_leading_silence(x.reverse()).reverse()
        strip_silence = lambda x: trim_trailing_silence(trim_leading_silence(x))
        origDuration = audio_file.duration_seconds * audio_file.frame_rate
        origSampleRate = audio_file.frame_rate
        frameCount = len(audio_file.get_array_of_samples())

        if options:
            if options['transpose'] or options['pitchShift']:
                # audio_file = audio_file.transpose(options['transpose'])
                y, sr = sf.read(self.filename)

                shiftSteps = 0

                if options['transpose']:
                    shiftSteps = options['transpose'] * 100
                if options['pitchShift']:
                    shiftSteps += options['pitchShift']
                
                y_pitch = librosa.effects.pitch_shift(y, sr=origSampleRate, n_steps=shiftSteps, bins_per_octave=1200)
                audio_file = librosaToPydub((y_pitch, origSampleRate))

            if options['normalize']:
                audio_file = audio_file.normalize()
            if options['trim']:
                audio_file = strip_silence(audio_file)
            if options['reverse']:
                audio_file = audio_file.reverse()
            if options['pan']:
                audio_file = audio_file.pan(options['pan'] / 100)
            if options['volume']:
                audio_file = audio_file + options['volume']

            if options['filter1On']:
                print(options)
                if options['filter1Type'] == 'lp':
                    audio_file = audio_file.low_pass_filter(cutoff_freq=options['filter1Freq'], order=options['filter1Order'])
                if options['filter1Type'] == 'hp':
                    audio_file = audio_file.high_pass_filter(cutoff_freq=options['filter1Freq'], order=options['filter1Order'])
            
            if options['filter2On']:
                if options['filter2Type'] == 'lp':
                    audio_file = audio_file.low_pass_filter(cutoff_freq=options['filter2Freq'], order=options['filter2Order'])
                if options['filter2Type'] == 'hp':
                    audio_file = audio_file.high_pass_filter(cutoff_freq=options['filter2Freq'], order=options['filter2Order'])

            if 'startOffset' in options or 'endOffset' in options:
                startOffset = int(options['startOffset'] if options['startOffset'] else 0)
                endOffset = int(options['endOffset'] if options['endOffset'] else 0)
                origFrames = int(options['frames'] if 'frames' in options else 0)

                if origFrames > 0 and origFrames - endOffset > startOffset:
                    # the percentage that is cut off from the start
                    startPct = startOffset / origFrames
                    # the percentage that is cut off from the end
                    endPct = endOffset / origFrames

                    newAudio = chop(audio_file, startPct, endPct)
                    audio_file = newAudio

            if 'fadeIn' in options:
                fadeInPct = int(options['fadeIn'])

                if fadeInPct > 0:
                    fadeIn = int(len(audio_file) * (int(options['fadeIn']) / 100))
                    audio_file = audio_file.fade_in(fadeIn)

            if 'fadeOut' in options:
                fadeOutPct = int(options['fadeOut'])

                if fadeOutPct > 0:
                    audio_file = audio_file.fade_out(int(len(audio_file) * (fadeOutPct / 100)))

        self.audio_file = audio_file

    def audio(self):
        return self.audio_file

    def export(self):
        """ Save the processed sample as an mp3 file """

        buffer = io.BytesIO()
        self.audio_file.export(buffer, format='mp3')
        mp3_data = buffer.getvalue()

        return mp3_data
    
    def info(self):
        """ Return a dict of information about the sample """
        return {
            'length': int(round(self.audio_file.duration_seconds * 1000)),
            'channels': self.audio_file.channels,
            'frame_rate': self.audio_file.frame_rate,
            'sample_width': self.audio_file.sample_width,
            'frame_width': self.audio_file.frame_width,
            'rms': self.audio_file.rms
        }

if __name__ == '__main__':
    filename = sys.argv[1]

    processed = SampleProcess(filename)
    processed.export()