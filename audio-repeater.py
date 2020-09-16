from multiprocessing import Process, Pipe
from Track_Process import TrackProcess
from tkinter import *
import logging
import sys
import os

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # FATAL

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 88


class TrackBarUI(Canvas):
    TRACK_BAR_WIDTH = 380
    TRACK_BAR_HEIGHT = 70

    def __init__(self, master, change_track_start_frame):
        super().__init__(master, width=self.TRACK_BAR_WIDTH, height=self.TRACK_BAR_HEIGHT, bd=0, highlightthickness=0,
                         cursor="hand2")
        self.callback = change_track_start_frame
        self.pack()
        self.x_pointer = 0
        self.draw()

    def draw(self):
        self.create_rectangle(0, 0, self.TRACK_BAR_WIDTH, self.TRACK_BAR_HEIGHT, fill="#7866a8")
        self.create_rectangle(self.x_pointer, 0,  self.TRACK_BAR_WIDTH, self.TRACK_BAR_HEIGHT, fill="yellow")
        for x in range(4, self.TRACK_BAR_WIDTH-1, 4):
            if x % 10 == 0:
                self.create_line(x, self.TRACK_BAR_HEIGHT, x, self.TRACK_BAR_HEIGHT - 22)
            self.create_line(x, self.TRACK_BAR_HEIGHT, x, self.TRACK_BAR_HEIGHT-12)

        self.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        self.x_pointer = event.x
        self.draw()
        self.callback(self.TRACK_BAR_WIDTH / event.x)


class App:
    def __init__(self, track_path):
        super().__init__()
        self.root = Tk()
        self.timer_value = IntVar(self.root, value=1000)
        self.root.after(100, self.interval_timer_update_call)
        parent_conn, child_conn = Pipe()
        self.conn = parent_conn
        self.track_process = TrackProcess(track_path, child_conn, get_logger("Track Process"))
        self.draw_ui()
        self.track_process.start()
        Process(target=establish_listen_manager, args=(self.conn,)).start()

        self.root.mainloop()

    def interval_timer_update_call(self):
        self.update_timer()
        self.root.after(1000, self.interval_timer_update_call)

    def update_timer(self):
        self.conn.send("GetCurrentTime")
        seconds = self.conn.recv()
        self.timer_value.set("{:02d}:{:02d}".format(*divmod(seconds, 60)))

    def change_start_frame(self, start_point_ratio):
        self.conn.send("NewStartFrameRatio %s" % start_point_ratio)
        self.update_timer()

    def replay(self, e=None):
        self.conn.send("Replay")

    def draw_ui(self):
        track_bar_f = Frame(self.root, bg="#323232")
        track_bar_f.pack(side=BOTTOM, fill="x")
        TrackBarUI(track_bar_f, self.change_start_frame)

        data_frame = Frame(self.root, bg="#d2d2d2", height="20")
        data_frame.pack(side=BOTTOM, fill="x")
        l1 = Label(data_frame, textvariable=self.timer_value)
        l1.pack()

        Button(text="FLAT", relief=FLAT)
        self.root.bind("<space>", self.replay)
        self.root.title("Audio Repeater")
        self.root.geometry("%sx%s" % (WINDOW_WIDTH, WINDOW_HEIGHT))

    def start(self):
        self.track_process.start()


def establish_listen_manager(conn):
    import user_listener as ul

    p_parent, p_child = Pipe()
    Process(target=ul.listener, args=(p_child,)).start()
    Process(target=ul.analyzer, args=(conn, p_parent, get_logger("analyzer"))).start()


def get_logger(name):
    logger = logging.getLogger(name)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)
    return logger


def main():
    if not len(sys.argv) > 1:
        print("No WAV file path has been defined, use ->  `python audioi-repeater.py audio.wav`")
        exit(1)
    if sys.argv[1].split(".")[-1] != "wav":
        print("Invalid file extension, only wav supported!")
        exit(1)
    if not os.path.exists(sys.argv[1]):
        print("File not found ->", sys.argv[1])
        exit(1)

    app = App(sys.argv[1])


if __name__ == '__main__':
    main()
