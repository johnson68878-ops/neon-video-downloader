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


class MultiProviderTests(unittest.TestCase):
    def test_all_services_have_https_web_and_local_icons(self):
        from neon.meetings import PROVIDERS
        from PIL import Image
        from pathlib import Path
        self.assertEqual(len(PROVIDERS), 5)
        for provider in PROVIDERS:
            self.assertTrue(provider.web.startswith('https://'))
            with Image.open(Path('assets/meetings')/provider.icon) as im:
                im.verify()

    def test_default_paths_respect_install_drive_and_spaces(self):
        from neon.meetings import BY_KEY, candidate_files
        with patch.dict('os.environ', {'APPDATA':r'D:/User Data/Roaming','ProgramFiles':r'E:/Program Files'}):
            values=[str(p).replace('\\','/') for p in candidate_files(BY_KEY['zoom'])]
            self.assertIn('D:/User Data/Roaming/Zoom/bin/Zoom.exe',values)
            self.assertIn('E:/Program Files/Zoom/bin/Zoom.exe',values)

    def test_teams_registered_protocol_does_not_require_fixed_exe(self):
        from neon.meetings import BY_KEY, find_local
        with patch('neon.meetings.registered_protocol',side_effect=lambda s:s=='msteams'):
            result=find_local(BY_KEY['teams'],{})
        self.assertEqual(result.kind,'protocol')
        self.assertEqual(result.value,'msteams:/l/meeting/new')

    def test_google_meet_uses_installed_pwa_shortcut(self):
        from neon.meetings import BY_KEY, find_local
        from pathlib import Path
        with patch('neon.meetings.start_menu_shortcuts',return_value=iter([Path('Google Meet.lnk')])):
            result=find_local(BY_KEY['google-meet'],{})
        self.assertEqual(result.kind,'shortcut')

    def test_every_missing_app_opens_its_own_web_after_notice(self):
        from neon.meetings import PROVIDERS, open_provider
        for p in PROVIDERS:
            order=[]
            with patch('neon.meetings.find_local',return_value=None), patch('neon.meetings.webbrowser.open',side_effect=lambda *a,**k:order.append(a[0]) or True):
                self.assertEqual(open_provider(p.key,lambda *a:order.append('notice')),'web')
            self.assertEqual(order,['notice',p.web])

    def test_broken_launch_falls_back_and_direct_web_skips_detection(self):
        from neon.meetings import LocalTarget, open_provider
        with patch('neon.meetings.find_local',return_value=LocalTarget('missing.exe','file')), patch('neon.meetings.os.startfile',side_effect=OSError()), patch('neon.meetings.webbrowser.open',return_value=True) as web:
            self.assertEqual(open_provider('zoom',Mock()),'web')
            web.assert_called_once()
        with patch('neon.meetings.find_local') as find, patch('neon.meetings.webbrowser.open',return_value=True):
            self.assertEqual(open_provider('teams',Mock(),True),'web')
            find.assert_not_called()

    def test_user_path_save_reset_and_bad_file(self):
        from neon.meetings import save_override,load_overrides,find_local,BY_KEY
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td, patch('neon.meetings.config_path',return_value=Path(td)/'config.json'):
            exe=Path(td)/'Zoom Custom.exe';exe.touch()
            save_override('zoom',str(exe))
            self.assertEqual(find_local(BY_KEY['zoom']).value,str(exe.resolve()))
            bad=Path(td)/'bad.cmd';bad.touch()
            with self.assertRaises(ValueError):save_override('zoom',str(bad))
            save_override('zoom',None)
            self.assertNotIn('zoom',load_overrides())

    def test_corrupt_settings_do_not_prevent_detection(self):
        from neon.meetings import load_overrides
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/'settings.json';file.write_text('broken')
            with patch('neon.meetings.config_path',return_value=file):self.assertEqual(load_overrides(),{})
