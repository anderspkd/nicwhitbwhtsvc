from flask import Flask, request, jsonify
from video import VideoPlayer

app = Flask(__name__, static_url_path='/static')

video = None

@app.route('/')
def index():
    return app.send_static_file('index.html')


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
