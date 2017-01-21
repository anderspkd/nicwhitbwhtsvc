from flask import Flask, request, jsonify
from functools import wraps
from video import VideoPlayer
import re

app = Flask(__name__)

video = None

@app.route('/')
def index():
    return('Hi :-)\n')


@app.route('/play', methods=['POST'])
def play_video():

    global video

    if video:
        if video.is_playing():
            return('Stop current video before playing a new one.\n')
        else:
            print('Cleaning up after last video...')
            video.clean_up()
            video = None

    data = request.get_json(force=True)
    if 'url' in data:
        try:
            fetch = bool(data['remote'])
        except:
            fetch = False
        video = VideoPlayer(data['url'], fetch=fetch)

    return('ok\n')


# Stop is synonymous with quit/exit
@app.route('/stop', methods=['GET'])
def stop_video():

    global video

    if video:
        video.controller.quit()
        video.clean_up()
        video = None

    return('ok\n')


@app.route('/pause', methods=['GET'])
def pause_video():

    global video

    if video:
        video.controller.pause()

    return('ok\n')


@app.route('/resume', methods=['GET'])
def resume_video():

    global video

    if video:
        video.controller.play()

    return('ok\n')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
