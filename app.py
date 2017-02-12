from flask import Flask, request, jsonify
from video import VideoPlayer

app = Flask(__name__)

import logging
formatter = logging.Formatter('%(asctime)s %(name)-15.15s %(levelname)-5.5s - %(message)s')
root_logger = logging.getLogger()
fh = logging.FileHandler('output.log')
fh.setFormatter(formatter)
root_logger.addHandler(fh)
root_logger.setLevel(logging.DEBUG)

logger = logging.getLogger('video')

video = None

@app.route('/play', methods=['POST'])
def play_video():

    global video

    if video:
        if video.is_playing():
            return('Stop current video before playing a new one.\n')
        else:
            logger.info('Cleaning up after last video...')
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
