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
