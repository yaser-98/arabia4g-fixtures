#!/usr/bin/env python3
"""Build a public fixture list from football-data.org, preserving optional manual links.
Only fixtures/schedules: no discovery or redistribution of sports streams.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'docs' / 'matches.json'
MANUAL = ROOT / 'manual_matches.json'
TOKEN = os.getenv('FOOTBALL_DATA_TOKEN', '').strip()
COMPS = [x.strip().upper() for x in os.getenv('COMPETITIONS', 'PL,PD,CL,SA,BL1,FL1').split(',') if x.strip()]


TEAM_AR = {
    "1. FC Köln": "كولن",
    "1. FC Union Berlin": "يونيون برلين",
    "1. FSV Mainz 05": "ماينز",
    "AC Milan": "ميلان",
    "AC Monza": "مونزا",
    "ACF Fiorentina": "فيورنتينا",
    "AFC Bournemouth": "بورنموث",
    "AJ Auxerre": "أوكسير",
    "AS Monaco FC": "موناكو",
    "AS Roma": "روما",
    "Angers SCO": "أنجيه",
    "Arsenal FC": "أرسنال",
    "Aston Villa FC": "أستون فيلا",
    "Atalanta BC": "أتالانتا",
    "Athletic Club": "أتلتيك بلباو",
    "Bayer 04 Leverkusen": "باير ليفركوزن",
    "Bologna FC 1909": "بولونيا",
    "Borussia Dortmund": "بوروسيا دورتموند",
    "Borussia Mönchengladbach": "بوروسيا مونشنغلادباخ",
    "Brentford FC": "برينتفورد",
    "Brighton & Hove Albion FC": "برايتون",
    "CA Osasuna": "أوساسونا",
    "Cagliari Calcio": "كالياري",
    "Chelsea FC": "تشيلسي",
    "Club Atlético de Madrid": "أتلتيكو مدريد",
    "Club Brugge KV": "كلوب بروج",
    "Como 1907": "كومو",
    "Coventry City FC": "كوفنتري سيتي",
    "Crystal Palace FC": "كريستال بالاس",
    "Deportivo Alavés": "ديبورتيفو ألافيس",
    "ES Troyes AC": "تروا",
    "Eintracht Frankfurt": "آينتراخت فرانكفورت",
    "Elche CF": "إلتشي",
    "Everton FC": "إيفرتون",
    "FC Augsburg": "أوغسبورغ",
    "FC Barcelona": "برشلونة",
    "FC Bayern München": "بايرن ميونخ",
    "FC Internazionale Milano": "إنتر ميلان",
    "FC Lorient": "لوريان",
    "FC Porto": "بورتو",
    "FC Schalke 04": "شالكه",
    "FK Bodø/Glimt": "بودو غليمت",
    "FK Shakhtar Donetsk": "شاختار دونيتسك",
    "Fenerbahçe SK": "فنربخشة",
    "Feyenoord Rotterdam": "فينورد",
    "Frosinone Calcio": "فروزينوني",
    "Fulham FC": "فولهام",
    "Galatasaray SK": "غلطة سراي",
    "Genoa CFC": "جنوى",
    "Getafe CF": "خيتافي",
    "Hamburger SV": "هامبورغ",
    "Hull City AFC": "هال سيتي",
    "Ipswich Town FC": "إيبسويتش تاون",
    "Juventus FC": "يوفنتوس",
    "LASK Linz": "لاسك لينز",
    "Le Havre AC": "لوهافر",
    "Le Mans FC": "لومان",
    "Leeds United FC": "ليدز يونايتد",
    "Levante UD": "ليفانتي",
    "Lille OSC": "ليل",
    "Liverpool FC": "ليفربول",
    "Manchester City FC": "مانشستر سيتي",
    "Manchester United FC": "مانشستر يونايتد",
    "Málaga CF": "ملقا",
    "Newcastle United FC": "نيوكاسل يونايتد",
    "Nottingham Forest FC": "نوتنغهام فورست",
    "OGC Nice": "نيس",
    "Olympique Lyonnais": "ليون",
    "Olympique de Marseille": "مارسيليا",
    "PAE AEK": "أيك أثينا",
    "PSV": "آيندهوفن",
    "Paris FC": "باريس إف سي",
    "Paris Saint-Germain FC": "باريس سان جيرمان",
    "Parma Calcio 1913": "بارما",
    "RB Leipzig": "لايبزيغ",
    "RC Celta de Vigo": "سيلتا فيغو",
    "RC Deportivo La Coruña": "ديبورتيفو لاكورونيا",
    "RC Strasbourg Alsace": "ستراسبورغ",
    "RCD Espanyol de Barcelona": "إسبانيول",
    "Racing Club de Lens": "لانس",
    "Rayo Vallecano de Madrid": "رايو فاييكانو",
    "Real Betis Balompié": "ريال بيتيس",
    "Real Madrid CF": "ريال مدريد",
    "Real Racing Club de Santander": "راسينغ سانتاندير",
    "Real Sociedad de Fútbol": "ريال سوسيداد",
    "SC Freiburg": "فرايبورغ",
    "SC Paderborn 07": "بادربورن",
    "SK Slavia Praha": "سلافيا براغ",
    "SS Lazio": "لاتسيو",
    "SSC Napoli": "نابولي",
    "SV 07 Elversberg": "إلفيرسبيرغ",
    "SV Werder Bremen": "فيردر بريمن",
    "Sabah FK": "صباح",
    "Sevilla FC": "إشبيلية",
    "Sporting Clube de Portugal": "سبورتينغ لشبونة",
    "Stade Brestois 29": "بريست",
    "Stade Rennais FC 1901": "رين",
    "Sunderland AFC": "سندرلاند",
    "TSG 1899 Hoffenheim": "هوفنهايم",
    "Torino FC": "تورينو",
    "Tottenham Hotspur FC": "توتنهام",
    "Toulouse FC": "تولوز",
    "US Lecce": "ليتشي",
    "US Sassuolo Calcio": "ساسولو",
    "Udinese Calcio": "أودينيزي",
    "Valencia CF": "فالنسيا",
    "Venezia FC": "فينيزيا",
    "VfB Stuttgart": "شتوتغارت",
    "Viking FK": "فيكينغ",
    "Villarreal CF": "فياريال",
    "ŠK Slovan Bratislava": "سلوفان براتيسلافا"
}

COMPETITION_AR = {
    "Premier League": "الدوري الإنجليزي الممتاز",
    "Primera Division": "الدوري الإسباني",
    "Bundesliga": "الدوري الألماني",
    "Serie A": "الدوري الإيطالي",
    "Ligue 1": "الدوري الفرنسي",
    "UEFA Champions League": "دوري أبطال أوروبا"
}

def fetch_matches(token, start, end, competition):
    url = 'https://api.football-data.org/v4/competitions/' + competition + '/matches?' + urlencode({'dateFrom': start, 'dateTo': end})
    req = Request(url, headers={'X-Auth-Token': token, 'User-Agent': 'Arabia4G-Fixtures/1.0', 'Accept': 'application/json'})
    with urlopen(req, timeout=22) as resp:
        return json.load(resp)['matches']


def translate_status(s):
    return {'FINISHED':'finished', 'CANCELLED':'cancelled', 'IN_PLAY':'live', 'PAUSED':'live', 'HALFTIME':'live', 'SUSPENDED':'cancelled'}.get(s)


def clean_manual():
    if not MANUAL.exists():
        return []
    data = json.loads(MANUAL.read_text(encoding='utf-8'))
    if not isinstance(data.get('matches'), list):
        raise ValueError('manual_matches.json needs matches array')
    return [m for m in data['matches'] if all(m.get(k) for k in ('home', 'away', 'kickoff', 'id'))]


def build(api_data, manual, now):
    # Keep all manually supplied matches; never publish links without 'verified' explicitly true.
    result = {str(m['id']): dict(m) for m in manual}
    for m in api_data:
        home = m.get('homeTeam') or {}
        away = m.get('awayTeam') or {}
        if not home.get('name') or not away.get('name') or not m.get('utcDate'):
            continue
        matchid = 'fd-' + str(m['id'])
        entry = {'id':matchid,
                 'home':TEAM_AR.get(home['name'], home['name']),
                 'away':TEAM_AR.get(away['name'], away['name']),
                 'home_en':home['name'], 'away_en':away['name'],
                 'competition':COMPETITION_AR.get((m.get('competition') or {}).get('name'), (m.get('competition') or {}).get('name') or 'كرة القدم'),
                 'kickoff':m['utcDate'], 'sources':[], 'origin':'football-data.org'}
        status = translate_status(m.get('status'))
        if status:
            entry['status'] = status
        # Explicitly preserve manual entries with matching provider id, e.g. verified sources.
        if matchid in result:
            prior = result[matchid]
            entry['sources'] = prior.get('sources') if isinstance(prior.get('sources'), list) else []
        result[matchid] = entry
    return {'timezone':'Asia/Aden', 'updated_at':now.isoformat(),
            'matches':sorted(result.values(), key=lambda x:x['kickoff'])}


def main():
    if not TOKEN:
        print('Missing FOOTBALL_DATA_TOKEN: configure GitHub repository secret before running.', file=sys.stderr)
        return 2
    now = datetime.now(timezone.utc)
    today = now.astimezone(ZoneInfo('Asia/Aden')).date()
    start = (today - timedelta(days=1)).isoformat()
    end = (today + timedelta(days=30)).isoformat()
    all_matches = []
    errors = []
    for c in COMPS:
        try:
            matches = fetch_matches(TOKEN, start, end, c)
            print(f'{c}: {len(matches)} events')
            all_matches.extend(matches)
        except Exception as exc:
            errors.append(f'{c}: {exc}')
    if errors:
        print('Failed sources: ' + '; '.join(errors), file=sys.stderr)
    # Do not overwrite the last working schedule when every API request fails.
    if not all_matches and errors:
        return 1
    doc = build(all_matches, clean_manual(), now)
    OUTPUT.parent.mkdir(exist_ok=True)
    serialized = json.dumps(doc, ensure_ascii=False, indent=2) + '\n'
    OUTPUT.write_text(serialized, encoding='utf-8')
    print(f'Saved {len(doc["matches"])} fixtures to {OUTPUT}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
