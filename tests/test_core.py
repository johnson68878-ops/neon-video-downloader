import unittest
from neon.urls import valid_urls, platform_name
from neon.downloader import options, QUALITY_CHOICES
from neon.worker import video_summary

class CoreTests(unittest.TestCase):
    def test_urls(self):
        self.assertEqual(valid_urls('https://example.com/v\n\nhttps://example.com/v'), ['https://example.com/v'])
        for value in ('', 'file:///secret', 'https://', 'hello'):
            with self.assertRaises(ValueError): valid_urls(value)
    def test_quality(self):
        o=options(dict(folder='downloads',quality='720p'))
        self.assertEqual(o['format'],'bv*[height<=?720]+ba/b[height<=?720]')
        self.assertTrue(o['noplaylist'])
    def test_audio_subtitles(self):
        o=options(dict(folder='downloads',quality='MP3 音訊',subtitles=True))
        self.assertEqual(o['postprocessors'][0]['preferredcodec'],'mp3')
        self.assertTrue(o['writesubtitles'])
    def test_share_text(self):
        self.assertEqual(valid_urls('看看這支影片 https://v.douyin.com/abc/ 複製後打開抖音'), ['https://v.douyin.com/abc/'])
        self.assertEqual(valid_urls('影片：https://www.youtube.com/watch?v=abc。'), ['https://www.youtube.com/watch?v=abc'])
    def test_platforms(self):
        for url, name in [('https://youtu.be/abc','YouTube'),('https://v.douyin.com/abc','抖音'),('https://fb.watch/abc','Facebook'),('https://vm.tiktok.com/abc','TikTok')]:
            self.assertEqual(platform_name(url),name)
        self.assertEqual(platform_name('https://youtube.com.example.org/video'),'其他網站 / 直接影片')
    def test_all_quality_limits(self):
        for quality in QUALITY_CHOICES:
            o=options(dict(folder='downloads',quality=quality))
            if quality.endswith('p'): self.assertIn('[height<=?'+quality[:-1]+']',o['format'])
        with self.assertRaises(ValueError): options(dict(folder='downloads',quality='bad'))
    def test_summary_omits_audio_and_sensitive_urls(self):
        result=video_summary({'title':'測試','url':'secret','formats':[{'height':1080,'vcodec':'avc1'},{'height':720,'vcodec':'avc1'},{'height':1080,'vcodec':'avc1'},{'height':999,'vcodec':'none'}]})
        self.assertEqual(result['heights'],[1080,720])
        self.assertNotIn('url', result)

if __name__=='__main__': unittest.main()
