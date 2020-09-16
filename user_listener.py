import pyaudio
import numpy as np
import librosa

p = pyaudio.PyAudio()
FORMAT = pyaudio.paInt16  # We use 16bit format per sample
CHANNELS = 1
CHUNK = 4096 # number of data points to read at a time
RATE = 44100 # time resolution of the recording device (Hz)
LIBROSA_COEFFICIENT = 32767
MINIMUM_AMPLITUDE = 0.01
RECORDING_SMOOTHER_FACTOR = 6 # This number account for smoothing the audio and not splitting it too aggressively
RECORDING_MINIMUM_AUDIO_FRAMES = RECORDING_SMOOTHER_FACTOR # Ignore sounds that are very short in (in milliseconds)
MODEL_BUFFER_LENGTH_REUIRED = 22292  #  to fit the model requirements (milliseconds)
MODEL_RECORDING_FRAMES_REQUIRED = 30 #  to fit the model requirements


def predict(audio):
    prob = model.predict(audio.reshape(1, MODEL_BUFFER_LENGTH_REUIRED, 1))
    index = np.argmax(prob[0])
    return index


def analyze_buffer(frames, logger):
    logger.info("Captured frames length -> %s", len(frames))

    # Check captured frames length is not more than required
    if len(frames) >= MODEL_RECORDING_FRAMES_REQUIRED:
        return

    logger.info("Analyzing...")

    # fit frames to convention
    extra = MODEL_RECORDING_FRAMES_REQUIRED - len(frames)
    frames = np.vstack((np.array(frames), np.zeros((extra, CHUNK), dtype=np.int16)))

    buffer = b"".join(frames)
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.short) / LIBROSA_COEFFICIENT
    samples = librosa.resample(samples, RATE, 8000)
    samples = (samples * LIBROSA_COEFFICIENT).astype(np.int16)

    res = predict(samples)
    logger.info("Prediction result -> %s" % res)
    return res


def listener(q):
    def get_frame(stream):
        data = stream.read(CHUNK)
        return np.frombuffer(data, dtype=np.int16)

    min_amplitude = LIBROSA_COEFFICIENT * MINIMUM_AMPLITUDE
    frames = []
    try:
        # start Recording
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
        while True:
            f = get_frame(stream)
            # If the the absolute sum of the frame values (amplitude height) larger than min_amplitude, sound detected
            if abs(sum(f)) > min_amplitude:
                s_count = 0
                frames = [f]
                # keeps record until there are RECORDING_SMOOTHER_FACTOR frames in a row that does not detect sound
                while s_count < RECORDING_SMOOTHER_FACTOR:
                    f = get_frame(stream)
                    frames.append(f)
                    if abs(sum(f)) > min_amplitude:
                        s_count = 0
                    else:
                        s_count += 1

                # Check sound not too short
                if len(frames) >= RECORDING_MINIMUM_AUDIO_FRAMES:
                    q.send(frames)

            frames = []
    except Exception as e:
        raise e


def analyzer(conn, listener_pipe, logger):
    global model
    import tensorflow as tf

    config = tf.compat.v1.ConfigProto()
    config.gpu_options.allow_growth = True
    sess = tf.compat.v1.Session(config=config)

    from keras.models import load_model

    model = load_model('model.hdf5')

    while True:
        if analyze_buffer(listener_pipe.recv(), logger) == 1:
            conn.send("VoiceTriggerDetected")
