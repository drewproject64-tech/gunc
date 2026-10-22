"""Turkish information bot. Python 3.12+, standard library only."""
import json
import logging
import os
import signal
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
NAME = 'Güncel Bağlantı Rehberi'
DESCRIPTION = 'Güncel bağlantı bilgilerini, erişim duyurularını ve bilgilendirici güncellemeleri tek bir yerden takip edin.'
ABOUT = 'Bağlantı bilgileri, duyurular ve bağlantı yapısını anlamanıza yardımcı olan Türkçe rehber.'
LABELS = ['Güncel Bilgiler', 'Duyurular', 'Yardım']
KEYBOARD = {'keyboard': [[{'text': label}] for label in LABELS], 'resize_keyboard': True, 'is_persistent': True}
WELCOME = (f'{NAME}’ne hoş geldiniz!\n\n'
           'Bağlantı rehberini okuyun, yayımlanan duyuruları inceleyin veya bir http/https bağlantısı göndererek alan adını ve yapısını öğrenin.\n\n'
           'Bu bot sitelerin güvenliğini veya erişilebilirliğini doğrulamaz. Aşağıdaki üç düğmeden birini seçin.')
HELP = ('Yardım\n\n/start — Ana menü\n/bilgiler — Bağlantı rehberi\n/duyurular — Yayımlanan duyurular\n/help — Kullanım bilgileri\n/privacy — Gizlilik\n\n'
        'Bir http:// veya https:// bağlantısı gönderin; alan adını, protokolünü ve dikkat edilecek noktaları açıklayalım. '
        'Bağlantı açılmaz, indirme yapılmaz ve güvenlik taraması uygulanmaz. Şifre, kimlik bilgisi veya özel erişim bağlantısı göndermeyin.')
PRIVACY = ('Gizlilik\n\nBu uygulama mesajlarınızı veya kullanıcı kimliklerinizi bir veritabanına kaydetmez. '
           'Gönderdiğiniz bağlantılar yalnızca yanıt oluşturmak için işlenir ve ziyaret edilmez. '
           'Telegram mesajları kendi gizlilik politikası kapsamında işler. Bot kendiliğinden reklam veya toplu mesaj göndermez.')


def load_content():
    data = json.loads((ROOT / 'content.json').read_text(encoding='utf-8'))
    for key in ('guide', 'announcements'):
        if not isinstance(data.get(key), list) or not all(isinstance(x, str) and x.strip() for x in data[key]):
            raise ValueError(f'content.json: {key} must be a list of nonempty strings')
        if len('\n\n'.join(data[key])) > 3400:
            raise ValueError(f'content.json: {key} exceeds 3400 characters')
    return data


def inspect_link(text):
    if len(text) > 2000 or any(c.isspace() for c in text):
        return 'Lütfen boşluk içermeyen, en fazla 2000 karakterlik tek bir http/https bağlantısı gönderin.'
    try:
        parts = urlsplit(text)
        host = parts.hostname
        port = parts.port
        if parts.scheme.lower() not in ('http', 'https') or not host:
            raise ValueError('invalid URL')
    except ValueError:
        return 'Bağlantı okunamadı. http:// veya https:// ile başlayan geçerli bir bağlantı gönderin.'
    notes = ['HTTPS bağlantıyı şifreler; sitenin güvenilir olduğunu tek başına kanıtlamaz.' if parts.scheme.lower() == 'https' else 'HTTP bağlantısı şifreli değildir. Hassas bilgi girmeyin.']
    if parts.username is not None:
        notes.append('Adreste kullanıcı bilgisi bulunuyor. Gerçek sunucu alan adı aşağıda gösterilmiştir.')
    if parts.query:
        notes.append('Sorgu parametreleri var; kişisel bilgi veya takip kodu içerebilir.')
    if 'xn--' in host or not host.isascii():
        notes.append('Uluslararası alan adı kullanılıyor; benzer görünen harflere dikkat edin.')
    return (f'Bağlantı bilgileri\n\nAlan adı: {host}\nProtokol: {parts.scheme.upper()}\n'
            + (f'Port: {port}\n' if port else '') + '\n' + '\n'.join(notes)
            + '\n\nBu sonuç bir güvenlik veya erişilebilirlik doğrulaması değildir. Site ziyaret edilmedi.')


def response(text, content):
    text = (text or '').strip()
    command = text.split()[0].split('@')[0].lower() if text else ''
    if command in ('/start', '/menu'):
        return WELCOME
    if text == LABELS[0] or command == '/bilgiler':
        return 'Güncel Bilgiler\n\n' + '\n\n'.join(content['guide'])
    if text == LABELS[1] or command == '/duyurular':
        return 'Duyurular\n\n' + ('\n\n'.join(content['announcements']) or 'Henüz yayımlanmış bir hizmet duyurusu yok. Bağlantı rehberini ve bağlantı açıklama özelliğini kullanabilirsiniz.')
    if text == LABELS[2] or command == '/help':
        return HELP
    if command == '/privacy':
        return PRIVACY
    if text.lower().startswith(('http://', 'https://')):
        return inspect_link(text)
    return 'Aşağıdaki menüden bir bölüm seçin veya incelemek için bir http/https bağlantısı gönderin. Yardım: /help'


class APIError(Exception):
    def __init__(self, code, retry_after=0):
        self.code, self.retry_after = code, retry_after
        super().__init__(f'Telegram API status {code}')


def api(token, method, **payload):
    req = Request(f'https://api.telegram.org/bot{token}/{method}',
                  data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=40) as result:
            data = json.load(result)
    except HTTPError as exc:
        try:
            data = json.loads(exc.read())
        except (ValueError, UnicodeError):
            raise APIError(exc.code) from None
    if not data.get('ok'):
        raise APIError(data.get('error_code', 500), data.get('parameters', {}).get('retry_after', 0))
    return data['result']


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    token = os.environ.get('BOT_TOKEN', '').strip()
    if not token:
        raise SystemExit('Set BOT_TOKEN in the hosting environment before starting.')
    content = load_content()
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        api(token, 'getMe')
        if api(token, 'getWebhookInfo').get('url'):
            raise SystemExit('An existing webhook is active. Remove it deliberately before using polling.')
        for language in ('', 'tr'):
            api(token, 'setMyName', name=NAME, language_code=language)
            api(token, 'setMyDescription', description=DESCRIPTION, language_code=language)
            api(token, 'setMyShortDescription', short_description=ABOUT, language_code=language)
        api(token, 'setMyCommands', commands=[{'command': c, 'description': d} for c, d in
            [('start', 'Ana menüyü aç'), ('bilgiler', 'Bağlantı rehberini oku'), ('duyurular', 'Duyuruları oku'), ('help', 'Yardım al'), ('privacy', 'Gizlilik bilgilerini oku')]])
    except (APIError, URLError, TimeoutError):
        raise SystemExit('Startup failed. Check connectivity and BOT_TOKEN; credentials were not logged.') from None
    offset = 0
    delay = 1
    logging.info('Bot started. Run exactly one polling instance.')
    while running:
        try:
            updates = api(token, 'getUpdates', offset=offset, timeout=25, allowed_updates=['message'])
            for update in updates:
                msg = update.get('message', {})
                if msg.get('chat', {}).get('type') == 'private':
                    try:
                        api(token, 'sendMessage', chat_id=msg['chat']['id'], text=response(msg.get('text'), content),
                            reply_markup=KEYBOARD, link_preview_options={'is_disabled': True})
                    except APIError as exc:
                        if exc.code not in (400, 403):
                            raise
                        logging.warning('Skipped undeliverable response: %s', exc.code)
                offset = update['update_id'] + 1
            delay = 1
        except APIError as exc:
            if exc.code in (401, 409):
                logging.error('Polling stopped: %s. Check token or duplicate instances.', exc.code)
                return
            time.sleep(min(max(delay, exc.retry_after), 60))
            delay = min(delay * 2, 30)
        except (URLError, TimeoutError, OSError, ValueError):
            logging.warning('Temporary connection failure; retrying.')
            time.sleep(delay)
            delay = min(delay * 2, 30)


if __name__ == '__main__':
    main()
