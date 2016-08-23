from flask import Flask, request, jsonify
import video as v

app = Flask(__name__)

current_video = None

@app.route('/video/play', methods=['POST'])
def video_play():

    global current_video

    url = request.form['url']

    if current_video is not None:
        if current_video.PLAYING:
            return jsonify({'error' : 'Video already playing'})

    current_video = v.Video(url, video_program='mpv')
    current_video.play()

    return jsonify({'playing' : current_video.info['title']})


@app.route('/video/stop', methods=['GET'])
def video_stop():

    global current_video

    msg = ''

    if current_video is not None:
        if current_video.PLAYING:
            current_video.stop()
            current_video = None
            msg = 'video stopped'
        else:
            msg = 'no video to stop'
    else:
        msg = 'no video to stop'

    return jsonify({'message' : msg})


@app.route('/video/changeres', methods=['PUT'])
def video_changeres():

    global current_video

    msg = ''
    resolution = request.form['resolution']

    if current_video is not None:

        current_video.stop()
        current_video.play(res=resolution)

        msg = 'changed resolution'

    else:

        msg = 'no video playing'

    return jsonify({'message' : msg})


@app.route('/video/playing', methods=['GET'])
def video_playing():

    global current_video

    msg = ''

    if current_video is not None:
        if current_video.PLAYING:
            msg = 'Playing ' + current_video.info['title']
        else:
            msg = 'Nothing playing'
    else:
        msg = 'Nothing playing'

    return jsonify({'message' : msg})


@app.route('/video/status', methods=['GET'])
def video_status():

    global current_video

    if current_video:
        return jsonify({'video' : current_video.info})
    else:
        return jsonify({'video' : current_video})


@app.route('/')
def index():

    return """Interface:
    /video/status
    /video/play
    /video/stop
    """

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
