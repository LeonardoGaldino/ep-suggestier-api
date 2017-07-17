# encoding: utf-8
from django.core.management.base import BaseCommand, CommandError
from app_suggestier.models import Episode, Season, Serie
import requests
import json
from multiprocessing import Process, Queue
from os import listdir
from os.path import isfile, realpath, dirname, join
from app_suggestier.populate_script import getSerieInfo

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'
    OMDB_URL = 'http://www.omdbapi.com/'
    GOOGLE_URL = 'https://translation.googleapis.com/language/translate/v2'
    blockQueue = Queue()
    dir_name = dirname(dirname(dirname(realpath(__file__))))

    def __init__(self):
        BaseCommand.__init__(self)
        with open(join(self.dir_name, 'api_keys.json')) as api_key_json:
            data = json.load(api_key_json)
            self.GOOGLE_API_KEY = data['google_key']
            self.OMDB_API_KEY = data['omdb_key']

    def parse_awards(self, awards):
        if awards == 'N/A':
            return 'Nenhum prêmio'
        return awards

    def fetch_ep_info(self, serie_name, season, ep):
        params = {
            't': serie_name,
            'season': season,
            'episode': ep,
            'type': 'episode',
            'apikey': self.OMDB_API_KEY,
            'plot': 'full'
        }
        try:
            res = requests.get(self.OMDB_URL, params=params)
        except:
            raise StopIteration('timeout')

        if res.ok:
            data = json.loads(res.content)
            try:
                ep_data = {
                    'title': data['Title'],
                    'season': str(season),
                    'ep': str(ep),
                    'time': data['Runtime'],
                    'grade': data['imdbRating'],
                    'spoiler': data['Plot'],
                    'awards': parse_awards(data['Awards']),
                    'year': data['Year'],
                    'more': 'http://www.imdb.com/title/' + data['imdbID']
                 }
            except:
                raise ValueError('title_error')

            return ep_data
        else:
            raise StopIteration('timeout')

    def fetch_num_seasons(self, serie_name):
        params = {
            't': serie_name,
            'apikey': self.OMDB_API_KEY,
            'type': 'series'
        }
        try:
            res = requests.get(self.OMDB_URL, params=params)
        except:
            raise StopIteration('timeout')
        if res.ok:
            data = json.loads(res.content)
            if data['Response'] == 'False':
                raise ValueError('Serie not found')
            return {
                    'num_seasons': data['totalSeasons'],
                    'poster': data['Poster']
                    }
        else:
            raise StopIteration('timeout')

    def fetch_num_eps(self, serie_name, season):
        params = {
            't': serie_name,
            'apikey': self.OMDB_API_KEY,
            'season': season,
            'type': 'series'
        }
        try:
            res = requests.get(self.OMDB_URL, params=params)
        except
            raise StopIteration('timeout')
        if res.ok:
            return len(json.loads(res.content)['Episodes'])
        else:
            res.raise_for_status()

    def random_number(self, min, max):
        return randint(int(min), int(max))

    def translate(self, input_str):
        params = {
            'key': self.GOOGLE_API_KEY,
            'q': self.input_str,
            'target': 'pt-br'
        }
        try:
            res = requests.get(self.GOOGLE_URL, params)
        except:
            raise StopIteration('timeout')
        trans = json.loads(res.content)
        return trans['data']['translations'][0]['translatedText']

    def populate_work(self):
        while not self.blockQueue.empty():
            serie_info = self.blockQueue.get()
            seasons = serie_info['seasons']
            print ('taking serie '+serie_info['serie_name'])
            while True:
                try:
                    try:
                        poster = self.fetch_num_seasons(serie_info['serie_name'])['poster']
                    except (StopIteration, ValueError) as e:
                        if str(e) == 'Serie not found':
                            print 'Serie not found ', serie_info['serie_name']
                            break
                        print 'RESTARTING1 ', serie_info['serie_name']
                        continue
                    cur_serie = Serie(title=serie_info['serie_name'], poster=poster, seasons=[])
                    for j in xrange(0, len(seasons)):
                        cur_season = Season(season_number=seasons[j]['seq'], episodes=[])
                        episodes = seasons[j]['episodes']
                        for k in xrange(0, len(episodes)):
                            try:
                                ep = self.fetch_ep_info(serie_info['serie_name'], seasons[j]['seq'], episodes[k]['seq'])
                            except (StopIteration, ValueError) as e:
                                if str(e) != 'title_error':
                                    k -= 1
                                    print 'RESTARTING2 ', serie_info['serie_name']
                                continue
                            cur_ep = Episode(title=ep['title'], ep_number=ep['ep'],year=ep['year'],
                                description=ep['spoiler'], grade=ep['grade'],
                                duration=ep['time'], awards=ep['awards'],
                                netflix_id=episodes[k]["episodeId"], imdb_id=ep['more'])
                            cur_season.episodes.append(cur_ep)
                        cur_serie.seasons.append(cur_season)
                    cur_serie.save()
                    print 'salvou ' + serie_info['serie_name']
                    break
                except (ValueError, IOError, KeyError) as e:
                    print 'erro em '
                    print e
                    break
                break

    def handle(self, *args, **options):
        print 'Populating BD!'
        series_dir = join(self.dir_name, 'series')
        series = [f for f in listdir(series_dir) if isfile(join(series_dir, f))]
        num_working_processes = 10

        for i in xrange(0, len(series)):
            serie_info = getSerieInfo(join(series_dir, series[i]))
            if not serie_info:
                continue
            self.blockQueue.put(serie_info, True)

        for i in xrange(0, num_working_processes):
            t = Process(target=self.populate_work)
            t.start()