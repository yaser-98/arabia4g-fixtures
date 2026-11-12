#!/usr/bin/env python3
"""Add national-team fixtures from API-Football to docs/matches.json.
Keeps the existing football-data.org and manually entered fixtures untouched.
One API-Football request per run (48/day at a twice-hourly schedule).
"""
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'docs' / 'matches.json'
KEY = os.environ.get('API_FOOTBALL_KEY', '').strip()

TEAM_AR = {
    'Yemen': 'اليمن', 'Saudi Arabia': 'السعودية', 'Oman': 'عُمان',
    'United Arab Emirates': 'الإمارات', 'UAE': 'الإمارات', 'Qatar': 'قطر',
    'Bahrain': 'البحرين', 'Kuwait': 'الكويت', 'Iraq': 'العراق',
    'Jordan': 'الأردن', 'Palestine': 'فلسطين', 'Syria': 'سوريا',
    'Lebanon': 'لبنان', 'Iran': 'إيران', 'Japan': 'اليابان',
    'South Korea': 'كوريا الجنوبية', 'Korea Republic': 'كوريا الجنوبية',
    'North Korea': 'كوريا الشمالية', 'China': 'الصين',
    'Australia': 'أستراليا', 'Uzbekistan': 'أوزبكستان',
    'Indonesia': 'إندونيسيا', 'Vietnam': 'فيتنام', 'Thailand': 'تايلاند',
    'India': 'الهند', 'Malaysia': 'ماليزيا', 'Tajikistan': 'طاجيكستان',
    'Kyrgyzstan': 'قيرغيزستان', 'Turkmenistan': 'تركمانستان',
    'Afghanistan': 'أفغانستان', 'Pakistan': 'باكستان',
    'Egypt': 'مصر', 'Morocco': 'المغرب', 'Algeria': 'الجزائر',
    'Tunisia': 'تونس', 'Libya': 'ليبيا', 'Sudan': 'السودان',
    'Mauritania': 'موريتانيا', 'Somalia': 'الصومال',
    'Djibouti': 'جيبوتي', 'Comoros': 'جزر القمر',
    'Senegal': 'السنغال', 'Nigeria': 'نيجيريا', 'Ghana': 'غانا',
    'Ivory Coast': 'ساحل العاج', "Côte d'Ivoire": 'ساحل العاج',
    'Cameroon': 'الكاميرون', 'Mali': 'مالي', 'Guinea': 'غينيا',
    'South Africa': 'جنوب أفريقيا', 'DR Congo': 'الكونغو الديمقراطية',
    'Congo DR': 'الكونغو الديمقراطية', 'Congo': 'الكونغو',
    'Burkina Faso': 'بوركينا فاسو', 'Cape Verde': 'الرأس الأخضر',
    'Cabo Verde': 'الرأس الأخضر', 'Uganda': 'أوغندا',
    'Kenya': 'كينيا', 'Tanzania': 'تنزانيا', 'Zambia': 'زامبيا',
    'Zimbabwe': 'زيمبابوي', 'Angola': 'أنغولا',
    'England': 'إنجلترا', 'Scotland': 'اسكتلندا', 'Wales': 'ويلز',
    'Northern Ireland': 'أيرلندا الشمالية', 'Republic of Ireland': 'أيرلندا',
    'Ireland': 'أيرلندا', 'France': 'فرنسا', 'Germany': 'ألمانيا',
    'Spain': 'إسبانيا', 'Italy': 'إيطاليا', 'Portugal': 'البرتغال',
    'Netherlands': 'هولندا', 'Belgium': 'بلجيكا', 'Switzerland': 'سويسرا',
    'Austria': 'النمسا', 'Denmark': 'الدنمارك', 'Sweden': 'السويد',
    'Norway': 'النرويج', 'Finland': 'فنلندا', 'Iceland': 'آيسلندا',
    'Poland': 'بولندا', 'Czech Republic': 'التشيك', 'Czechia': 'التشيك',
    'Slovakia': 'سلوفاكيا', 'Croatia': 'كرواتيا', 'Serbia': 'صربيا',
    'Slovenia': 'سلوفينيا', 'Bosnia and Herzegovina': 'البوسنة والهرسك',
    'Bosnia & Herzegovina': 'البوسنة والهرسك', 'Montenegro': 'الجبل الأسود',
    'Albania': 'ألبانيا', 'Kosovo': 'كوسوفو',
    'North Macedonia': 'مقدونيا الشمالية', 'Greece': 'اليونان',
    'Turkey': 'تركيا', 'Türkiye': 'تركيا', 'Ukraine': 'أوكرانيا',
    'Romania': 'رومانيا', 'Hungary': 'المجر', 'Bulgaria': 'بلغاريا',
    'Georgia': 'جورجيا', 'Armenia': 'أرمينيا',
    'Azerbaijan': 'أذربيجان', 'Israel': 'إسرائيل',
    'Cyprus': 'قبرص', 'Malta': 'مالطا', 'Luxembourg': 'لوكسمبورغ',
    'Lithuania': 'ليتوانيا', 'Latvia': 'لاتفيا', 'Estonia': 'إستونيا',
    'Belarus': 'بيلاروسيا', 'Moldova': 'مولدوفا',
    'Russia': 'روسيا', 'Kazakhstan': 'كازاخستان',
    'Brazil': 'البرازيل', 'Argentina': 'الأرجنتين',
    'Uruguay': 'أوروغواي', 'Colombia': 'كولومبيا',
    'Chile': 'تشيلي', 'Peru': 'بيرو', 'Ecuador': 'الإكوادور',
    'Paraguay': 'باراغواي', 'Bolivia': 'بوليفيا',
    'Venezuela': 'فنزويلا', 'USA': 'الولايات المتحدة',
    'United States': 'الولايات المتحدة', 'Mexico': 'المكسيك',
    'Canada': 'كندا', 'Costa Rica': 'كوستاريكا',
    'Panama': 'بنما', 'Jamaica': 'جامايكا', 'Honduras': 'هندوراس',
    'El Salvador': 'السلفادور', 'Guatemala': 'غواتيمالا',
    'Nicaragua': 'نيكاراغوا', 'Haiti': 'هايتي', 'Cuba': 'كوبا',
    'Trinidad and Tobago': 'ترينيداد وتوباغو',
    'Antigua and Barbuda': 'أنتيغوا وبربودا',
    'Aruba': 'أروبا', 'Martinique': 'مارتينيك',
    'Curaçao': 'كوراساو', 'Curacao': 'كوراساو',
    'Dominican Republic': 'جمهورية الدومينيكان',
    'New Zealand': 'نيوزيلندا', 'Fiji': 'فيجي',
}

LEAGUE_AR = {
    'UEFA Nations League': 'دوري الأمم الأوروبية',
    'CONCACAF Nations League': 'دوري أمم الكونكاكاف',
    'World Cup': 'كأس العالم',
    'World Cup - Qualification Europe': 'تصفيات كأس العالم - أوروبا',
    'World Cup - Qualification Asia': 'تصفيات كأس العالم - آسيا',
    'World Cup - Qualification Africa': 'تصفيات كأس العالم - أفريقيا',
    'World Cup - Qualification South America': 'تصفيات كأس العالم - أمريكا الجنوبية',
    'World Cup - Qualification CONCACAF': 'تصفيات كأس العالم - الكونكاكاف',
    'Friendlies': 'مباريات ودية للمنتخبات',
    'Euro Championship': 'بطولة أمم أوروبا',
    'Africa Cup of Nations': 'كأس أمم أفريقيا',
    'Asian Cup': 'كأس آسيا',
    'Copa America': 'كوبا أمريكا',
    'CONCACAF Gold Cup': 'الكأس الذهبية للكونكاكاف',
    'Gold Cup': 'الكأس الذهبية للكونكاكاف',
    'Arab Cup': 'كأس العرب',
    'Gulf Cup of Nations': 'كأس الخليج',
}

# Competition titles must clearly indicate a national-team tournament.
# This deliberately does not ingest all games, such as 3rd-division clubs.
ALLOW_NAME = re.compile(
    r'(?i)(?:nations\s+league|world\s+cup|euro\s+championship|'
    r'africa\s+cup\s+of\s+nations|asian\s+cup|copa\s+america|'
    r'gold\s+cup|arab\s+cup|gulf\s+cup|friendlies|'
    r'qualification|qualifiers|olympic\s+games)'
)
BLOCK_NAME = re.compile(r'(?i)club\s+friendlies|friendly\s+clubs|reserve|\bu[- ]?(?:17|19|20|21|23)\b')

STATUS = {
    'NS': None, 'TBD': None, '1H': 'live', 'HT': 'live',
    '2H': 'live', 'ET': 'live', 'BT': 'live', 'P': 'live',
    'FT': 'finished', 'AET': 'finished', 'PEN': 'finished',
    'CANC': 'cancelled', 'ABD': 'cancelled',
    'PST': 'postponed', 'SUSP': 'postponed', 'INT': 'postponed',
}


def is_national_competition(league):
    name = str((league or {}).get('name') or '')
    country = str((league or {}).get('country') or '')
    if BLOCK_NAME.search(name) or not ALLOW_NAME.search(name):
        return False
    # Avoid domestic competition names that happen to include 'World Cup' etc.
    # CONCACAF Nations League uses the regional name and qualifies as international.
    return country.lower() in ('world', 'international', 'europe', 'africa', 'asia',
                               'south america', 'north & central america',
                               'north america', 'concacaf', '') or bool(
                                   re.search(r'(?i)nations league|world cup|qualification|qualifiers', name))


def normal(text):
    s = unicodedata.normalize('NFKD', str(text or ''))
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9\u0600-\u06ff]+', '', s.lower())


def normdate(timestamp):
    try:
        return datetime.fromisoformat(str(timestamp).replace('Z', '+00:00')).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def duplicate(entry, existing):
    # Detect overlap even when provider IDs differ, but only when names align.
    # Aliases are compared in English where available, not Arabic-only labels.
    eh, ea = normal(entry.get('home_en')), normal(entry.get('away_en'))
    t = normdate(entry.get('kickoff'))
    if not t or not eh or not ea:
        return False
    for prev in existing:
        old = normdate(prev.get('kickoff'))
        if not old or abs((t - old).total_seconds()) > 7200:
            continue
        ph = normal(prev.get('home_en', prev.get('home')))
        pa = normal(prev.get('away_en', prev.get('away')))
        if (eh, ea) == (ph, pa) or (eh, ea) == (pa, ph):
            return True
    return False


def convert(game):
    fx = game.get('fixture') or {}
    league = game.get('league') or {}
    teams = game.get('teams') or {}
    home = str((teams.get('home') or {}).get('name') or '').strip()
    away = str((teams.get('away') or {}).get('name') or '').strip()
    kickoff = fx.get('date')
    fid = fx.get('id')
    if not home or not away or not kickoff or not fid:
        return None
    # Avoid fixtures with an explicitly undefined kickoff time.
    st = (fx.get('status') or {}).get('short')
    if st == 'TBD':
        return None
    comp = str(league.get('name') or 'منتخبات')
    entry = {
        'id': 'af-' + str(fid),
        'home': TEAM_AR.get(home, home), 'away': TEAM_AR.get(away, away),
        'home_en': home, 'away_en': away,
        'competition': LEAGUE_AR.get(comp, comp),
        'kickoff': kickoff, 'sources': [], 'origin': 'api-football',
    }
    value = STATUS.get(st)
    if value:
        entry['status'] = value
    return entry


def main():
    if not KEY:
        print('Missing API_FOOTBALL_KEY: keeping existing fixtures.', file=sys.stderr)
        return 0
    if not OUTPUT.exists():
        print('Missing docs/matches.json; run update_matches.py first.', file=sys.stderr)
        return 1
    doc = json.loads(OUTPUT.read_text(encoding='utf-8'))
    old = doc.get('matches')
    if not isinstance(old, list):
        raise ValueError('docs/matches.json must contain a matches list')
    today = datetime.now(ZoneInfo('Asia/Aden')).date()
    params = urlencode({'from': (today - timedelta(days=1)).isoformat(),
                        'to': (today + timedelta(days=30)).isoformat(),
                        'timezone': 'Asia/Aden'})
    url = 'https://v3.football.api-sports.io/fixtures?' + params
    req = Request(url, headers={'x-apisports-key': KEY, 'Accept': 'application/json',
                                'User-Agent': 'Arabia4G-Fixtures/1.0'})
    try:
        with urlopen(req, timeout=40) as response:
            payload = json.load(response)
    except Exception as ex:
        print(f'API-Football request failed: {ex}; keeping club schedule.', file=sys.stderr)
        return 0
    if payload.get('errors'):
        print('API-Football errors: ' + str(payload['errors']) + '; keeping club schedule.', file=sys.stderr)
        return 0
    games = payload.get('response') or []
    paging = payload.get('paging') or {}
    if int(paging.get('total') or 1) > 1:
        print('Warning: API-Football has multiple pages; only first page was read.', file=sys.stderr)
    selected = []
    for game in games:
        if not is_national_competition(game.get('league')):
            continue
        entry = convert(game)
        if entry and not duplicate(entry, old) and not duplicate(entry, selected):
            selected.append(entry)
    doc['matches'] = sorted(old + selected, key=lambda m: m.get('kickoff') or '')
    OUTPUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'API-Football returned {len(games)} fixtures; added {len(selected)} international fixtures; total {len(doc["matches"])}.')
    print(f'Quota remaining today: {payload.get("response_remaining", "see API dashboard")}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
