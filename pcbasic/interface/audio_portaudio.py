"""
PC-BASIC - audio_portaudio.py
Sound interface based on PortAudio

(c) 2015, 2016 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import os
import logging
import Queue
from collections import deque
from contextlib import contextmanager

try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    import numpy
except ImportError:
    numpy = None

from ..basic.base import signals
from . import base
from . import synthesiser


@contextmanager
def suppress_output():
    """Suppress stdout and stderr messages from linked library."""
    # http://stackoverflow.com/questions/977840/redirecting-fortran-called-via-f2py-output-in-python/978264#978264
    # open file descriptors to /dev/null
    null_fds = [os.open(os.devnull, os.O_RDWR) for x in xrange(2)]
    # save the file descriptors for /dev/stdout and /dev/stderr
    save = os.dup(1), os.dup(2)
    # put /dev/null fds on 1 (stdout) and 2 (stderr)
    os.dup2(null_fds[0], 1)
    os.dup2(null_fds[1], 2)
    # do stuff
    yield
    # restore file descriptors
    os.dup2(save[0], 1)
    os.dup2(save[1], 2)
    # close the /dev/null fds
    os.close(null_fds[0])
    os.close(null_fds[1])


class AudioPortAudio(base.AudioPlugin):
    """SDL2-based audio plugin."""

    # approximate generator chunk length
    # one wavelength at 37 Hz is 1192 samples at 44100 Hz
    chunk_length = 1192 * 4

    def __init__(self, audio_queue):
        """Initialise sound system."""
        if not pyaudio:
            logging.warning('PyAudio module not found. Failed to initialise PortAudio audio plugin.')
            raise base.InitFailed()
        if not numpy:
            logging.warning('NumPy module not found. Failed to initialise PortAudio audio plugin.')
            raise base.InitFailed()
        # synthesisers
        self.signal_sources = synthesiser.get_signal_sources()
        # sound generators for each voice
        self.generators = [deque(), deque(), deque(), deque()]
        # buffer of samples; drained by callback, replenished by _play_sound
        self._samples = [numpy.array([], numpy.int16) for _ in range(4)]
        self._dev = None
        base.AudioPlugin.__init__(self, audio_queue)

    def __enter__(self):
        """Perform any necessary initialisations."""
        with suppress_output():
            self._dev = pyaudio.PyAudio()
            sample_format = self._dev.get_format_from_width(2)
            bufsize = 1024
            self._min_samples_buffer = 2*bufsize
            #self._samples = [numpy.zeros(bufsize*2, numpy.int16) for _ in range(4)]
            self._stream = self._dev.open(format=sample_format, channels=1,
                    rate=synthesiser.sample_rate, output=True,
                    frames_per_buffer=bufsize,
                    stream_callback=self._get_next_chunk)
            self._stream.start_stream()
            base.AudioPlugin.__enter__(self)

    def __exit__(self, type, value, traceback):
        """Close down PortAudio."""
        self._stream.stop_stream()
        self._stream.close()
        self._dev.terminate()
        return base.AudioPlugin.__exit__(self, type, value, traceback)

    def tone(self, voice, frequency, duration, fill, loop, volume):
        """Enqueue a tone."""
        self.generators[voice].append(synthesiser.SoundGenerator(
                    self.signal_sources[voice], synthesiser.feedback_tone,
                    frequency, duration, fill, loop, volume))

    def noise(self, source, frequency, duration, fill, loop, volume):
        """Enqueue a noise."""
        feedback = synthesiser.feedback_noise if source else synthesiser.feedback_periodic
        self.generators[3].append(synthesiser.SoundGenerator(
                    self.signal_sources[3], feedback,
                    frequency, duration, fill, loop, volume))

    def hush(self):
        """Stop sound."""
        for voice in range(4):
            self.next_tone[voice] = None
            while self.generators[voice]:
                self.generators[voice].popleft()
        self._samples = [numpy.array([], numpy.int16) for _ in range(4)]

    def work(self):
        """Replenish sample buffer."""
        for voice in range(4):
            if len(self._samples[voice]) > self._min_samples_buffer:
                # nothing to do
                continue
            while True:
                if self.next_tone[voice] is None or self.next_tone[voice].loop:
                    try:
                        # looping tone will be interrupted by any new tone appearing in the generator queue
                        self.next_tone[voice] = self.generators[voice].popleft()
                    except IndexError:
                        if self.next_tone[voice] is None:
                            current_chunk = None
                            break
                current_chunk = self.next_tone[voice].build_chunk(self.chunk_length)
                if current_chunk is not None:
                    break
                self.next_tone[voice] = None
            if current_chunk is not None:
                # append chunk to samples list
                # should lock to ensure callback doesn't try to access the list too?
                self._samples[voice] = numpy.concatenate(
                        (self._samples[voice], current_chunk))

    def _get_next_chunk(self, in_data, length, time_info, status):
        """Callback function to generate the next chunk to be played."""
        # this is for 16-bit samples
        samples = [self._samples[voice][:length] for voice in range(4)]
        self._samples = [self._samples[voice][length:] for voice in range(4)]
        # if samples have run out, add silence
        for voice in range(4):
            if len(samples[voice]) < length:
                silence = numpy.zeros(length-len(samples[voice]), numpy.int16)
                samples[voice] = numpy.concatenate((samples[voice], silence))
        # mix the samples by averaging
        # we need the int32 intermediate step, for int16 numpy will average [32767, 32767] to -1
        mixed = numpy.array(numpy.mean(samples, axis=0, dtype=numpy.int32), dtype=numpy.int16)
        return mixed.data, pyaudio.paContinue
