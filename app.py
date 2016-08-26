from flask import Flask, request, jsonify
from video import VideoPlayer

app = Flask(__name__)

current_video = None

@app.route('/play', methods=['POST'])
def video_play():

    global current_video
    data = request.get_json()

    if current_video is not None:
        return('Stop current video first!')

    if data is not None:

        try:
            video = data['url']
        except KeyError:
            return('No video link provided!')
        try:
            fetch = data['fetch']
        except:
            fetch = False

        current_video = VideoPlayer(video, fetch_with_ytdl=fetch)

    return('OK')


@app.route('/stop', methods=['GET'])
def video_stop():

    global current_video

    if current_video is not None:
        current_video.stop()
        current_video = None
        return('OK')
    else:
        return('No video to stop')


@app.route('/pause', methods=['GET'])
def video_pause():

    global current_video

    if current_video is not None:
        current_video.pause()
        return('OK')
    else:
        return('No video to pause')


@app.route('/resume', methods=['GET'])
def video_resume():

    global current_video

    if current_video is not None:
        current_video.play()
        return('OK')
    else:
        return('No video to resume')

@app.route('/')
def index():

    return('hi')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
