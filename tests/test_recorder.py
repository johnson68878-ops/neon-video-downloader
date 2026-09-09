import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from neon.recorder import Recorder, video_command


class RecorderTests(unittest.TestCase):
    def test_negative_monitor_origin_and_odd_region(self):
        command = video_command((-1920, 0, 1279, 719), 720, True, 'out.mkv')
        self.assertEqual(command[command.index('-offset_x')+1], '-1920')
        self.assertIn('1279x719', command)
        self.assertIn('scale=-2:718', command[command.index('-vf')+1])
        self.assertEqual(command[command.index('-crf')+1], '29')

    def test_resolution_cap_and_readable_mode(self):
        command = video_command((0, 0, 3840, 2160), 1080, False, 'out.mkv')
        self.assertIn('scale=-2:1080', command[command.index('-vf')+1])
        self.assertEqual(command[command.index('-crf')+1], '24')

    def test_invalid_region_rejected(self):
        with self.assertRaises(ValueError):
            video_command((0, 0, 0, 1080), 720, True, 'out.mkv')

    def test_empty_recording_is_not_published(self):
        with tempfile.TemporaryDirectory() as directory:
            r = Recorder(directory, (0, 0, 640, 360), system=False)
            with self.assertRaises(RuntimeError):
                r.finish()
            self.assertFalse(r.output.exists())
            self.assertTrue(r.work.exists())

    def test_merge_failure_preserves_segments(self):
        with tempfile.TemporaryDirectory() as directory:
            r = Recorder(directory, (0, 0, 640, 360), system=False)
            segment = r.work/'segment-0.mp4'; segment.write_bytes(b'recoverable data')
            r.segments = [segment]
            with patch('neon.recorder.run_ffmpeg', side_effect=RuntimeError('disk full')):
                with self.assertRaises(RuntimeError): r.finish()
            self.assertEqual(segment.read_bytes(), b'recoverable data')
            self.assertFalse(r.output.exists())

    def test_success_only_removes_own_session(self):
        with tempfile.TemporaryDirectory() as directory:
            r = Recorder(directory, (0, 0, 640, 360), system=False)
            unrelated = Path(directory)/'existing.mp4'; unrelated.write_bytes(b'original')
            segment = r.work/'segment-0.mp4'; segment.write_bytes(b'segment')
            r.segments = [segment]
            def mux(args, log): Path(args[-1]).write_bytes(b'finished')
            with patch('neon.recorder.run_ffmpeg', side_effect=mux):
                result = r.finish()
            self.assertEqual(result.read_bytes(), b'finished')
            self.assertEqual(unrelated.read_bytes(), b'original')
            self.assertFalse(r.work.exists())
