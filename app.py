from flask import Flask, request, jsonify
from video import VideoPlayer
from util import as_bool, us2string

app = Flask(__name__)

import logging
formatter = logging.Formatter('%(asctime)s %(name)-15.15s %(levelname)-7.7s - %(message)s')
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
        url = data['url']

        fetch = as_bool(data.get('fetch', False))
        force = as_bool(data.get('force', False))

        video = VideoPlayer(data['url'], fetch=fetch, force_fetch=force)
        logger.info('Playing %s', video)
        return(video.title)

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

@app.route('/status', methods=['GET'])
def video_status():
    global video
    if video:
        pos = video.controller.position()
        dur = video.controller.duration()
        return(us2string(dur - pos))

    return('ok\n')

@app.route('/metadata', methods=['GET'])
def video_metadata():
    global video
    if video:
        video.controller.metadata()
    return('ok\n')

@app.route('/seek', methods=['POST'])
def video_seek():
    global video
    if video:
        data = request.get_json(force=True)
        offset = data.get('offset', False)
        unit = data.get('unit', 's')
        if offset:
            return str(video.controller.seek(offset, unit=unit))
    return('ok\n')
