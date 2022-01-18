import pyaudio
from rev_ai.models import MediaConfig
from rev_ai.streamingclient import RevAiStreamingClient
from six.moves import queue
import ast
from flask_restful import Resource
import wave
import time, os
import sys
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
# from ..functions.microphone import MicrophoneStream


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


class Record(Resource):
  def get(self):
      """
      Sampling rate of your microphone and desired chunk size
      """
      rate = 44800
      chunk = 4480

      """
      Insert your access token here
      """
      access_token = '0279uPVzAIeEJgFjn-EvhWxP9vXnGwQvT04h1H_DSWQdLOHoceN7k3e74FNDcsnPj7GkZSYcyCUMBnJ4w6bDCnj52Etvk'

      """
      Creates a media config with the settings set for a raw microphone input
      """
      example_mc = MediaConfig('audio/x-raw', 'interleaved', 44100, 'S16LE', 1)

      streamclient = RevAiStreamingClient(access_token, example_mc)

      """
      Opens microphone input. The input will stop after a keyboard interrupt.
      """


      with MicrophoneStream(rate, chunk) as stream:

          response_gen = streamclient.start(stream.generator())

          """
          Iterates through responses and prints them
          """
          try:

              max_time = 7
              start_time = time.time() 
              live_text = []
              for response in response_gen:
                  responses =  response
                  results = ast.literal_eval(responses)
                  spoken = [ i['value'] for i in results['elements']]
                  live_text.append(spoken)
      #             finals = ''.join(finals)
                  for items in spoken:
      #                 print(items, end =' ')
                      print(items.ljust(os.get_terminal_size().columns + 1), end="\r")
                  if time.time() - start_time > max_time:
                      streamclient.end()
                      pass
      #         responses =  responses
          except BrokenPipeError:
              sys.tracebacklimit = 0
              result = ast.literal_eval(responses)
              final = [ i['value'] for i in result['elements']]
              final = ''.join(final)
              print('actual text', final)
              resp = ast.literal_eval(responses)
              df = pd.DataFrame(columns=['Words', 'start_time', 'end_time'])
              for i in resp['elements']:
                  if i.get('ts') or i.get('end_ts'):
                      df = df.append({'Words':i['value'], 'start_time':i['ts'], 'end_time':i['end_ts']}, ignore_index=True)
            #   df.dropna(how='any')
            #   title = {'Article_titlt':title}
            #   summary = {'Summarized_text':summarized}
            #     # category = { 'Article_category': categorized}
            #   result = []
            #   result.append(title)
            #   result.append(summary)
          try:
              data = {
                  'Live_streaming': live_text,
                  'Actual_spoken_words': final
              }

              return {
                  'status': 'success',
                  'data': data,
                  'message': 'spoken words transcribed, thanks',
              }, 200

          except Exception as e:

                print(str(e))
                return {
                    'status': 'failed',
                    'data': None,
                    'message': str(e)
                }, 500


  #We need a principal data scientist to manage our project in the country at large
