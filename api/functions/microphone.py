from rev_ai.streamingclient import RevAiStreamingClient
from six.moves import queue
import ast
import wordninja
import wave
import time, os
import sys
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

class MicrophoneStream(object):
    
    """
    Opens a recording stream as a generator yielding the audio chunks.
    """
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            )
        
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        
        frames = []
        
        RECORD_SECONDS = 5
        for i in range(0, int(self._rate / self._chunk * RECORD_SECONDS)):
            data = self._audio.read(self._chunk)
            frames.append(data)
        print ("finished recording")


        # stop Recording
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        
        self._audio.stop_stream()
        self._audio.close()
        self.closed = True
        
#         self._audio_interface.terminate()
        WAVE_OUTPUT_FILENAME = 'stream.wav'
        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(1)
        waveFile.setsampwidth(self._audio_interface.get_sample_size(pyaudio.paInt16))
        waveFile.setframerate(self._rate)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()
        """
        Signal the generator to terminate so that the client's
        streaming_recognize method will not block the process termination.
        """
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """
        Continuously collect data from the audio stream, into the buffer.
        """
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            """
            Use a blocking get() to ensure there's at least one chunk of
            data, and stop iteration if the chunk is None, indicating the
            end of the audio stream.
            """
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            """
            Now consume whatever other data's still buffered.
            """
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)
