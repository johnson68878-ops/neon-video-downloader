import unittest
from unittest.mock import Mock, patch
from neon.meetings import DEFAULT_CLIENT, WEB_URL, open_scheduler


class MeetingLaunchTests(unittest.TestCase):
    @patch('neon.meetings.webbrowser.open')
    @patch('neon.meetings.os.startfile')
    @patch('neon.meetings.find_client', return_value=DEFAULT_CLIENT)
    def test_installed_client_without_browser(self, find, start, web):
        notify = Mock()
        self.assertEqual(open_scheduler(notify), 'desktop')
        start.assert_called_once_with(str(DEFAULT_CLIENT))
        notify.assert_not_called(); web.assert_not_called()

    @patch('neon.meetings.webbrowser.open', return_value=True)
    @patch('neon.meetings.find_client', return_value=None)
    def test_missing_client_notifies_before_web(self, find, web):
        calls = []
        web.side_effect = lambda *args, **kw: calls.append('web') or True
        self.assertEqual(open_scheduler(lambda *args: calls.append('notice')), 'web')
        self.assertEqual(calls, ['notice', 'web'])
        web.assert_called_once_with(WEB_URL, new=2)

    @patch('neon.meetings.webbrowser.open', return_value=True)
    @patch('neon.meetings.os.startfile', side_effect=OSError('unavailable'))
    @patch('neon.meetings.find_client', return_value=DEFAULT_CLIENT)
    def test_broken_client_falls_back(self, find, start, web):
        notify = Mock()
        self.assertEqual(open_scheduler(notify), 'web')
        self.assertIn('無法啟動', notify.call_args.args[1])

    @patch('neon.meetings.webbrowser.open', return_value=False)
    @patch('neon.meetings.find_client', return_value=None)
    def test_browser_failure_provides_manual_url(self, find, web):
        with self.assertRaisesRegex(OSError, WEB_URL):
            open_scheduler(Mock())
