# audio-repeater

### Why did I do that?
not so long time ago I started to play guitar, every song I wanted to learn how to play I needed to work few times on each 
part of the song, and play on the guitar while the song part is playing too. <br /> and when the song part ends?
I needed to put down the guitar and go to the computer, and change the starting point in the media player, then quickly
take the guitar and start to play. Exhausting, inefficient... 
 
 
Long story short, we are developers, when something like that happen we find solution. And that's exactly what I did.

### In short
Quick app to play an audio starting from selected time point and replay it whenever you whistle.


### In long
The app is a very basic audio player with one more important feature, replay on voice command, specifficly, whistle. 
This feature relay on deep learning model I developed (explanation not here) that detect whenever the user whistle,
if whistle is detected the app will replay the song from the selected starting point.

### How to use

python audio-repeater.py "audio.wav"

Requirements, 
* Python3
* pyaudio
* librosa 0.8


Note: only wav files are supported for now.
