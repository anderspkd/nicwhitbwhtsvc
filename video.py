from __future__ import unicode_literals
import youtube_dl
from subprocess import Popen, PIPE

class Video:

    def __init__(self, url, video_program='mpv'):

        # Info object
        info = {}

        info['url'] = url

        self._video_program = video_program
        self._process = None

        self.PLAYING = False

        with youtube_dl.YoutubeDL() as ydl:
            result = ydl.extract_info(url, download=False)

        info['title'] = result['title'] if 'title' in result else "(!)Untitled Video"

        self._all_formats = result['formats'] if 'formats' in result else []

        formats = [x for x in self._all_formats if 'resolution' in x]

        def res_cmp(k): # crude resolution comparetor
            rs = k['resolution'].split('x')
            x = int(rs[0])
            y = int(rs[1])
            return x + y

        self._formats = sorted(formats, key=res_cmp, reverse=True)

        info['avaliable resolutions'] = [x['resolution'] for x in self._formats]
        info['resolution'] = None

        for v in self._formats:
            info[v['resolution']] = v

        self.info = info
        self._result = result


    def status(self):
        process = self._process
        if process is not None:
            process.poll()
            return p.returncode
        return None


    def play(self, res='best'):
        if self.PLAYING is False:

            vid = None

            if res == 'best':
                vid = self._formats[0]['url']
            else:
                try:
                    vid = self.info[res]['url']
                except KeyError:
                    print('resolution not found ' + res)
                    vid = self._formats[0]['url']

            self._process = Popen([self._video_program, vid], stdin=PIPE, universal_newlines=True)
            self.PLAYING = True


    def stop(self):
        if self.PLAYING is True:
            self._process.kill()
            self.PLAYING = False
