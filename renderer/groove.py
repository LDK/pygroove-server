# GOAL: Create a simple groovebox using pydub to render JSON sequences created via web
import copy
import io
import librosa
import soundfile as sf

import numpy as np
from pydub import AudioSegment
from .custom_effects import *
import cgitb
from os import curdir, rename
from os.path import join as pjoin

cgitb.enable()

# Beats per bar
beatDiv = 4
# Ticks per beat
tickDiv = 16
# Song length in bars
songBars = 0
# List of patterns to play, in order
songPatterns = []
# # Dict of tracks, keyed by name
# trackIndex = {}

filterMaxFreq = 22000

# Amount of swing to apply to patterns
# Starts getting crazy above 1, reasonably groovy at like .25.  Default to none.
swingAmount = 0;

# swingUp is an iterator that gets toggled with each note, to alternate the swing direction
# i.e., it swings up and then down, or back and then forth.  You get it.
swingUp = False

# Default channel volume and pan
channelDefaults = {'volume': -12.0, 'pan': 0}

current_offset_ms = 0  # Start at 0 ms

# Pitch indexes
pitchIndexes = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}

def pitch_diff(fromPitch, toPitch):
    for octave in range(9):
      if str(octave) in fromPitch:
          fromOctave = octave
          fromNote = fromPitch.replace(str(fromOctave),"")
      if str(octave) in toPitch:
          toOctave = octave
          toNote = toPitch.replace(str(toOctave),"")
    fromDiff = (toOctave - fromOctave) * 12
    fromNote = fromNote.upper()
    toNote = toNote.upper()
    fromDiff = fromDiff + (pitchIndexes[toNote] - pitchIndexes[fromNote])
    return fromDiff
    
# Takes a librosa-formatted (float32) audiofile and returns a pydub (int16) AudioSegment
# Adapted from https://stackoverflow.com/posts/68151661/revisions
def librosaToPydub(audiofile):
    y, sr = audiofile
    
    # convert from float to uint16
    y = np.array(y * (1<<15), dtype=np.int16)
    audio_segment = AudioSegment(
        y.tobytes(), 
        frame_rate=sr,
        sample_width=y.dtype.itemsize, 
        channels=1
    )
    return audio_segment

def detect_leading_silence(sound, silence_threshold=-50.0, chunk_size=10):
    trim_ms = 0 # ms

    assert chunk_size > 0 # to avoid infinite loop
    while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size

    return trim_ms

def trim(sound, silence_threshold=-50.0, chunk_size=10):
    start_trim = detect_leading_silence(sound, silence_threshold, chunk_size)
    end_trim = detect_leading_silence(sound.reverse(), silence_threshold, chunk_size)
    duration = len(sound)    
    trimmed_sound = sound[start_trim:duration-end_trim]
    return trimmed_sound

def newChannel(bpm:int, name = ''):
    global songPatterns

    # Length of the track is equal to number of bars times beats-per-bar times beat length times number of patterns
    trackLength = songBars * barLen(bpm)

    track = AudioSegment.silent(trackLength)
    if name:
        global channels
        channels[name] = track
    else:
        return track
    return 

# Length of a bar in milliseconds
def barLen(bpm:int):
    return (60/bpm) * 1000 * beatDiv

# Length of a beat in milliseconds
def beatLen(bpm:int):
    return (60/bpm) * 1000

# Length of a tick in milliseconds
def tickLen(bpm:int):
    return (60/bpm) * 1000 / tickDiv

# Add an instance of a sound at a location determined by bpm-based placement
def addNote(trackName,sound,bar,beat,tick,bpm,options = {}):
    global swingUp
    global channels
    if channels[trackName]:
        channel = channels[trackName]
    else:
        return
    # If swing is active and we are not on the very first tick of the pattern, apply swing
    if (swingAmount and (tick > 1 or beat > 1 or bar > 1)):
        if (swingUp):
            tick += swingAmount
        else:
            tick -= swingAmount
        swingUp = not swingUp
    loc = 0
    loc += tickLen(bpm) * (tick - 1)
    loc += beatLen(bpm) * (beat - 1)
    loc += barLen(bpm) * (bar - 1)
    loc = int(loc)

    # master = master.overlay(channels[trackName], position=current_offset_ms)
    soundLoc = float(int(loc) + int(current_offset_ms))
    channel = channel.overlay(sound, position=soundLoc, gain_during_overlay=-12.0)

    # print ("Adding note to track {} at {}".format(trackName,soundLoc))

    channels[trackName] = channel

def chop(sound:AudioSegment, startPct:float, endPct:float):
    slices = []

    # We will be cutting the AudioSegment into 3 pieces.
    # The first slice will be the first (startPct * 100)% of the original
    # The second slice will be the following ((1 - startPct - endPct) * 100)% of the original
    # The third slice will be the last (endPct * 100)% of the original
    
    # The first slice
    slices.append(sound[:int(round(startPct * len(sound)))])

    # The second slice
    slices.append(sound[int(round(startPct * len(sound))):int(round((1 - endPct) * len(sound)))])

    # The third slice
    slices.append(sound[int(round((1 - endPct) * len(sound))):])

    return slices[1]

def split(wavFile,pieces):
    soundLoc = './static/audio/uploaded/'+wavFile
    sound = AudioSegment.from_wav(soundLoc)
    slices = []
    sliceLen = int(len(sound) / pieces)
    for i, chunk in enumerate(sound[::sliceLen]):
        if (i >= pieces):
            break;
        sliceName = "./static/audio/uploaded/split/{fileName}-{num}.wav".format(fileName=wavFile.replace('.wav',''),num=i+1)
        sliceInfo = {'filename': sliceName, 'parent': soundLoc, 'start': i*sliceLen, 'end': (i+1)*sliceLen, 'len': len(chunk)}
        with open(sliceName, "wb") as f:
            chunk.export(f, format="wav")
            slices.append(sliceInfo)
    return slices

def getStepSound(step, track, bpm:int):
    trackWav = './static/audio/' + track['sample']['filename']
    stepSound = AudioSegment.from_wav(trackWav) - 12

    origLen = len(stepSound)

    shiftSteps = 0
    transposeSteps = 0

    rootPitch = track['rootPitch'] if 'rootPitch' in track else 'C3'

    playMode = track['playMode'] if 'playMode' in track else 'oneshot'

    if 'pitch' in step:
        transposeSteps += pitch_diff(rootPitch, step['pitch'])
        shiftSteps = transposeSteps * 100
    if 'transpose' in track:
        transposeSteps += int(track['transpose'])
        shiftSteps = transposeSteps * 100
    if 'pitchShift' in track:
        shiftSteps += int(track['pitchShift'])

    if shiftSteps != 0:
        y, sr = sf.read(trackWav)
        y_pitch = librosa.effects.pitch_shift(y, sr=sr, n_steps=shiftSteps, bins_per_octave=1200)

        stepSound = librosaToPydub((y_pitch, sr))

    duration = step['duration'] if 'duration' in step else 1
    stepLen = beatLen(bpm) * (duration / beatDiv)
    
    if 'normalize' in track:
        if (track['normalize'] == True):
            stepSound = stepSound.normalize()

    if 'trim' in track:
        if (track['trim'] == True):
            stepSound = trim(stepSound)

    if 'pan' in step and step['pan'] != 0:
        stepSound = stepSound.pan(step['pan']/100)
        # print ("Panning step to {}".format(step['pan'] / 100))
    else:
        if 'pan' in track and track['pan'] != 0:
            # print ("Panning track {} to {}".format(track['name'],track['pan'] / 100))
            stepSound = stepSound.pan(track['pan']/100)

    # Apply the volume
    if 'volume' in track:
        trackVol = float(track['volume'])
        stepSound += trackVol
        # print ("Applying volume of {} to track {}".format(trackVol,track['name']))

    if 'filters' in step and len(step['filters']) > 0:
        print ("Applying filters to step")
        print (step['filters'])

        for filter in step['filters']:
            if filter['on'] == True:
                if filter['filter_type'] == 'hp':
                    stepSound = stepSound.high_pass_filter(cutoff_freq=int(filter['frequency']), order=filter['order'] if 'order' in filter else 3)
                if filter['filter_type'] == 'lp':
                    # stepSound = stepSound.resonant_low_pass_filter(cutoff_freq=int(filter['frequency']), order=5, q=filter['q'])
                    stepSound = stepSound.low_pass_filter(cutoff_freq=int(filter['frequency']), order=filter['order'] if 'order' in filter else 3)
                # if filter['filter_type'] == 'bp':
                #     trackSound = trackSound.band_pass_filter(low_cutoff_freq=int(filter['frequency']), high_cutoff_freq=int(filter['frequency2']), order=3)
    else:
        if 'filters' in track:
            for filter in track['filters']:
                if filter['on'] == True:
                    if filter['filter_type'] == 'hp':
                        stepSound = stepSound.high_pass_filter(cutoff_freq=int(filter['frequency']), order=filter['order'] if 'order' in filter else 3)
                    if filter['filter_type'] == 'lp':
                        # stepSound = stepSound.resonant_low_pass_filter(cutoff_freq=int(filter['frequency']), q=filter['q'], order=filter['order'] if 'order' in filter else 3)
                        stepSound = stepSound.low_pass_filter(cutoff_freq=int(filter['frequency']), order=filter['order'] if 'order' in filter else 3)
                    # if filter['filter_type'] == 'bp':
                    #     trackSound = trackSound.band_pass_filter(low_cutoff_freq=int(filter['frequency']), high_cutoff_freq=int(filter['frequency2']), order=3)

    if 'reverse' in track:
        if (track['reverse'] == True):
            stepSound = stepSound.reverse()

    if 'reverse' in step:
        if (step['reverse'] == True):
            stepSound = stepSound.reverse()

    if 'startOffset' in track or 'endOffset' in track:
        startOffset = int(track['startOffset'] if 'startOffset' in track else 0)
        endOffset = int(track['endOffset'] if 'endOffset' in track else 0)
        origFrames = int(track['sample']['frames'] if 'frames' in track['sample'] else 0)

        if 'reverse' in step and step['reverse'] == True:
            startOffset, endOffset = endOffset, startOffset

        if origFrames > 0 and origFrames - endOffset > startOffset:
            # the percentage that is cut off from the start
            startPct = startOffset / origFrames
            # the percentage that is cut off from the end
            endPct = endOffset / origFrames

            stepSound = chop(stepSound, startPct, endPct)

    if playMode == 'hold':
        stepSound = stepSound[0:stepLen]
    elif playMode == 'loop':
        newSound = AudioSegment.silent(stepLen)

        framesAdded = 0

        while (framesAdded < stepLen):
            newSound = newSound.overlay(stepSound, position=framesAdded, times=1)
            framesAdded += len(stepSound)

        stepSound = newSound[0:stepLen]
    elif playMode == 'oneshot':
        stepSound = stepSound[0:origLen]
    elif playMode == 'pingpong':
        newSound = AudioSegment.silent(stepLen)

        i = 0
        framesAdded = 0

        while (framesAdded < stepLen):
            if (i % 2 == 0):
                newSound = newSound.overlay(stepSound, position=framesAdded, times=1)
            else:
                newSound = newSound.overlay(stepSound.reverse(), position=framesAdded, times=1)

            framesAdded += len(stepSound)
            i += 1

        stepSound = newSound[0:stepLen]

    if 'retrigger' in step:
        retrigCount = int(step['retrigger'])
        if retrigCount > 0:
            print ("Retriggering step {} times per beat (duration: {} beats)".format(retrigCount, duration))
            retrigCount = int(step['retrigger'])
            retrigLen = beatLen(bpm) / retrigCount
            retrigSound = AudioSegment.silent(beatLen(bpm) * duration / beatDiv)
            retrigClip = AudioSegment.silent(retrigLen)
            retrigClip = retrigClip.overlay(stepSound, position=0)

            print("retrigSound length is {}".format(len(retrigSound)))
            print("retrigClip length is {}".format(len(retrigClip)))
            print("stepSound length is {}".format(len(stepSound)))

            stepSound = retrigSound.overlay(retrigClip, position=0, times=retrigCount * duration)

    if 'fadeIn' in track:
        fadeInPct = int(track['fadeIn'])

        if fadeInPct > 0:
            fadeIn = int(len(stepSound) * (int(track['fadeIn']) / 100))
            stepSound = stepSound.fade_in(fadeIn)

    if 'fadeOut' in track:
        fadeOutPct = int(track['fadeOut'])

        if fadeOutPct > 0:
            fadeOut = int(len(stepSound) * (int(track['fadeOut']) / 100))
            stepSound = stepSound.fade_out(fadeOut)
    
    # If sound was trimmed, and not already faded...
    if origLen > len(stepSound) and not 'fadeOut' in track:
        # Do a slight fade-out to avoid any clicks
        stepSound = stepSound.fade_out(10)

    return stepSound

def renderStep(track, trackSound, step, bpm:int, startingBar = 1):
    trackName = track['name']
    loc = step['loc'].split('.')
    bar = int(loc[0]) + startingBar - 1
    beat = int(loc[1])
    tick = int(loc[2])
    
    # print ("Rendering step {} at bar {} beat {} tick {}".format(trackName,bar,beat,tick))
    # print ("Pattern starts at bar {}".format(startingBar))

    if trackSound == None:
        return

    sound = copy.copy(trackSound)
    
    # Apply the volume
    if ('velocity' in step):
        velocityOffset = float((step['velocity'] - 80) / 127)
        volumeDiff = velocityOffset * abs(track['volume']) if 'volume' in track else velocityOffset

        if volumeDiff:
            # print ("Applying velocity of {} to track {}".format(step['velocity'],track['name']))
            # print ("Velocity offset is {}".format(velocityOffset))
            # print ("Track volume is {}".format(track['volume']))
            # print ("Volume diff is {}".format(volumeDiff))

            sound = sound + (volumeDiff)
    
    # Apply the pan
    if ('pan' in step):
        sound = sound.pan(int(step['pan'])/100)
    
    # Add note
    addNote(trackName,sound,bar,beat,tick,bpm)

def renderPatternPreview(data):
    # Create a payload for renderJSON using only the data needed for the preview
    # data object will contain beatDiv, tickDiv, swing, tracks and a single-item pattern entry

    renderPattern = data['pattern']
    renderPattern['position'] = 1

    renderData = {
        'swing': data['swing'],
        'patterns': [renderPattern],
        'patternSequence': [{'position': 1, 'bar': 1}],
        'bpm': data['bpm'],
        'tracks': data['tracks'],
        'title': renderPattern['name']
    }

    return renderJSON(renderData)

def renderJSON(data):
    global channels, beatDiv, tickDiv, songBars, swingAmount, swingUp, channelDefaults, songPatterns, trackIndex, current_offset_ms

    # Dict of patterns, keyed by position
    patternIndex = {}

    # Reset all the globals
    trackIndex = {}
    channels = {}

    current_offset_ms = 0

    bpm = int(data['bpm'])

    def jumpToBar(bar):
        global current_offset_ms
        current_offset_ms = (bar - 1) * barLen(bpm)

    # beatDiv = int(data['beatDiv']), defaulting to 4 if beatDiv key is not present on data
    beatDiv = int(data['beatDiv']) if 'beatDiv' in data else beatDiv
    tickDiv = int(data['tickDiv']) if 'tickDiv' in data else tickDiv
    swingAmount = float(data['swing']) if 'swing' in data else swingAmount
    swingUp = False

    songPatterns = data['patternSequence'] if 'patternSequence' in data else []
    songBars = 0

    # For each pattern, add it to patternIndex
    for pattern in data['patterns']:
        patternIndex[pattern['position']] = pattern

    for patternEntry in songPatterns:
        pattern = patternIndex[int(patternEntry['position'])]
        bar = int(patternEntry['bar'])
        length = int(pattern['bars']) if 'bars' in pattern else 2

        if (bar + length - 1 > songBars):
            songBars = bar + length - 1

    print ("Song length is {} bars".format(songBars))

    # title = data['title']

    # Create the master track
    master = newChannel(bpm)

    # For each track in the json data, add a channel
    for track in data['tracks']:
        if 'disabled' in track and track['disabled'] == True:
            if track['name'] in trackIndex:
                # print ("Removing track {}".format(track['name']))
                del trackIndex[track['name']]
                del channels[track['name']]
            continue

        trackName = track['name']

        # print ("Adding track {}".format(trackName))

        # Add a channel
        newChannel(bpm, trackName)

        # Add to track index
        trackIndex[trackName] = track

    # For each pattern in songPatterns, for each track, add the notes, apply any filters, set the volume, set the pan and overlay onto master
    for patternEntry in songPatterns:
        pattern = patternIndex[int(patternEntry['position'])]

        for trackName, steps in pattern['steps'].items():
            if trackName in trackIndex:
                track = trackIndex[trackName]
                # print ("Rendering pattern {} track {}".format(position,trackName))
            else:
                continue

            for step in steps:
                stepSound = getStepSound(step, track, bpm)
                renderStep(track, stepSound, step, bpm, patternEntry['bar'])

    for trackName, track in channels.items():
        master = master.overlay(track, position=0, gain_during_overlay=-6)
        # print ("Overlaying track {}".format(trackName))

    # Create an in-memory buffer
    buffer = io.BytesIO()

    master.normalize().export(buffer, format='mp3', bitrate="320k")

    # Get the MP3 data from the buffer
    mp3_data = buffer.getvalue()

    # Write to file

    # get date string formatted like 20231231235959
    # datestring = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    # renderFilename = "{}".format('preview')

    # out_f = open("{}.mp3".format(renderFilename), 'wb')
    # out_f.write(mp3_data)

    master.normalize().export(buffer, format='mp3', bitrate="320k")

    # Close the buffer
    buffer.close()


    return mp3_data
