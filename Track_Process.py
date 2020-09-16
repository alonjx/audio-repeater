import threading
import pyaudio
import wave
import re
from multiprocessing import Process, Pipe

class Track:
    def __init__(self, track_path):
        pass
        self.track_file = wave.open(track_path, 'rb')

    def get_current_position(self):
        frames = self.track_file.getnframes()
        pos = self.track_file.tell()
        return frames / float(pos)

    def get_duration(self):
        frames = self.track_file.getnframes()
        rate = self.track_file.getframerate()
        return frames / float(rate)


class TrackConnectionHandlerThread(threading.Thread):
    def __init__(self, process):
        super().__init__()
        self.process = process

    def run(self):
        p = self.process
        while True:
            msg = p.conn.recv()
            msg_parts = re.findall("\S+", msg)
            if msg_parts[0] in ["Replay", "VoiceTriggerDetected"]:
                self.process.logger.info(msg)
                self.replay()
            elif msg_parts[0] == "NewStartFrameRatio":
                self.process.logger.info(msg)
                p.start_frame = int(p.track.track_file.getnframes() // float(msg_parts[1]))
                self.replay()
            elif msg_parts[0] == "GetCurrentTime":
                p.conn.send(int(p.track.track_file.tell() / p.track.track_file.getframerate()))


    def replay(self):
        self.process.track.track_file.setpos(self.process.start_frame)


class TrackProcess(Process):
    def __init__(self, track_path, conn, logger):
        super().__init__()
        self.conn = conn
        self.track_path = track_path
        self.start_frame = 0
        self.track = None
        self.conn_handler = None
        self.timer_handler = None
        self.logger = logger

    def replay(self):
        self.track_file.setpos(self.start_frame)

    def run(self):
        self.track = Track(self.track_path)
        self.conn_handler = TrackConnectionHandlerThread(self)

        self.conn_handler.start()
        self.play()

    def play(self):
        chunk = 1024

        # create an audio object
        p = pyaudio.PyAudio()

        f = self.track.track_file

        # open stream
        stream = p.open(format=
                        p.get_format_from_width(f.getsampwidth()),
                        channels=f.getnchannels(),
                        rate=f.getframerate(),
                        output=True)

        # read data
        data = f.readframes(chunk)

        # play stream
        while data != '':
            stream.write(data)
            data = f.readframes(chunk)

        stream.close()
        p.terminate()

