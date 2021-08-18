"""Everything used for downloading video in bilibili.com."""
import json
import re

from video_dl.spider import Spider
from video_dl.toolbox import info
from video_dl.video import Video, Media


class BilibiliSpider(Spider):
    """spider for bilibili."""
    site = 'bilibili.com'
    home_url = 'https://www.bilibili.com'

    # come re pattern to extract information from html source code
    re_initial_state = re.compile(r'window.__INITIAL_STATE__=(.*?);')
    re_playinfo = re.compile(r'window.__playinfo__=(.*?)</script>')

    def __init__(self):
        super().__init__()

        # from resolution id to description dictionary
        self.id2desc = None

    async def before_download(self) -> None:
        self.video = Video(self.session)
        await self.parse_html(self.url)
        self.video.choose_collection()

        self.video_list.append(self.video)

    def after_downloaded(self) -> None:
        for video in self.video_list:
            video.merge()

    async def parse_html(self, target_url: str) -> None:
        """extract key information from html source code.

        Args:
            target_url: target url copied from online vide website.
        """
        info('url', target_url)
        resp = await self.fetch_html(target_url)

        # get video's title and set file path
        state = json.loads(self.re_initial_state.search(resp).group(1))
        self.video.title = state['videoData']['title']

        playinfo = json.loads(self.re_playinfo.search(resp).group(1))
        if self.id2desc is None:
            desc = playinfo['data']['accept_description']
            quality = playinfo['data']['accept_quality']
            self.id2desc = {
                str(key): value for key, value in zip(quality, desc)
            }

        videos = playinfo['data']['dash']['video']
        for video in videos:
            self.video.add_media(Media(
                url=video['base_url'],
                size=video['bandwidth'],
                desc=self.id2desc[str(video['id'])] + ' + ' + video['codecs'],
            ), target='picture')

        audios = playinfo['data']['dash']['audio']
        for audio in audios:
            self.video.add_media(Media(
                url=audio['base_url'],
                size=audio['bandwidth']), target='sound')
