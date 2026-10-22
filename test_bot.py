import unittest
import bot


class BotTests(unittest.TestCase):
    def test_navigation_and_repeat_start(self):
        content = bot.load_content()
        for text in ['/start', '/start payload', '/start@ExampleBot', *bot.LABELS, '/help', '/privacy', None, 'hello']:
            result = bot.response(text, content)
            self.assertTrue(result)
            self.assertLess(len(result), 4096)
        self.assertEqual(bot.response('/start', content), bot.response('/start payload', content))
        self.assertEqual(len(bot.KEYBOARD['keyboard']), 3)

    def test_real_host_not_userinfo(self):
        result = bot.inspect_link('https://trusted.example@actual.example/path?secret=123')
        self.assertIn('Alan adı: actual.example', result)
        self.assertNotIn('secret=123', result)
        self.assertIn('kullanıcı bilgisi', result)

    def test_malformed_and_unencrypted(self):
        for url in ['https://', 'https://[broken', 'https://example.com:wrong']:
            self.assertIn('okunamadı', bot.inspect_link(url))
        self.assertIn('şifreli değildir', bot.inspect_link('http://example.com'))
        self.assertIn('boşluk', bot.inspect_link('https://example.com x'))

    def test_no_fabricated_announcements(self):
        self.assertIn('Henüz', bot.response('/duyurular', bot.load_content()))


if __name__ == '__main__':
    unittest.main()
