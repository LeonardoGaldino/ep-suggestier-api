# encoding: utf-8
from models import Episode, Season, Serie
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseRedirect
from random import randint
import requests
import json
from threading import Thread
from multiprocessing import Process, Queue
from os import listdir
from os.path import isfile, realpath, dirname, join
from populate_script import getSerieInfo

OMDB_URL = 'http://www.omdbapi.com/'
GOOGLE_URL = 'https://translation.googleapis.com/language/translate/v2'

special_series = {
	'HOW I MET YOUR MOTHER':{
		'ids': [(70218481,70218482),(70218503,70218504),(70218525,70218526),(70218545,70218546),(70218569,70218570),(70218593,70218594),(70259006,70259007),(70288864,70288865),(80010314,80010315)],
		'num_seasons': 9,
		'poster': 'https://images-na.ssl-images-amazon.com/images/M/MV5BMTA5MzAzNTcyNjZeQTJeQWpwZ15BbWU3MDUyMzE1MTk@._V1_SX300.jpg'
	},
	'DEXTER':{
		'ids': [(70085714,70085715), (70077035,70119583), (70206691,70206692), (70126613,70213516), (70249844,70249845), (70250623,70250624), (70261662,70261663), (70282442,70282443)],
		'num_seasons': 8,
		'poster': 'https://images-na.ssl-images-amazon.com/images/M/MV5BMTM5MjkwMTI0MV5BMl5BanBnXkFtZTcwODQwMTc0OQ@@._V1_SX300.jpg'
	},
	'TWO AND A HALF MEN':{
		'ids': [(80018877,80018878), (80018783,80018784), (80019007,80019008), (80018901,80018902), (80049390,80049391), (80049409,80049410), (80049289,80049290), (80049511,80049512)],
		'num_seasons': 8,
		'poster': 'https://images-na.ssl-images-amazon.com/images/M/MV5BMTcwMDU1MDExNl5BMl5BanBnXkFtZTcwOTAwMjYyOQ@@._V1_SX300.jpg'	
	}

}

def mapEpNum(serie, season, ep):
	if ep==1:
		return special_series[serie]['ids'][season][0]
	return (special_series[serie]['ids'][season][1] + ep - 2)

dir_name = dirname(realpath(__file__))

with open(join(dir_name, 'api_keys.json')) as api_key_json:
	data = json.load(api_key_json)
	GOOGLE_API_KEY = data['google_key']
	OMDB_API_KEY = data['omdb_key']

def parse_awards(awards):
	if awards == 'N/A':
		return 'Nenhum prêmio'
	return awards

def fetch_ep_info(serie_name, season, ep):
	params = {
		't': serie_name,
		'season': season,
		'episode': ep,
		'type': 'episode',
		'apikey': OMDB_API_KEY,
		'plot': 'full'
	}
	try:
		res = requests.get(OMDB_URL, params=params)
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


def fetch_num_seasons(serie_name):
	params = {
		't': serie_name,
		'apikey': OMDB_API_KEY,
		'type': 'series'
	}
	try:
		res = requests.get(OMDB_URL, params=params)
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

def random_number(min, max):
	return 1 if min == max else randint(int(min), int(max))

def fetch_num_eps(serie_name, season):
	params = {
		't': serie_name,
		'apikey': OMDB_API_KEY,
		'season': season,
		'type': 'series'
	}
	res = requests.get(OMDB_URL, params=params)
	if res.ok:
		return len(json.loads(res.content)['Episodes'])
	else:
		res.raise_for_status()

def translate(input_str):
	params = {
		'key': GOOGLE_API_KEY,
		'q': input_str,
		'target': 'pt-br'
	}
	trans = json.loads(requests.get(GOOGLE_URL, params).content)
	return trans['data']['translations'][0]['translatedText']

@require_http_methods(['GET'])
def v_random_ep2(request):
	content_type = "application/json; charset=utf-8; encoding=utf-8"
	if 'serie_name' in request.GET:
		name_serie = request.GET['serie_name'].upper()
		serie = Serie.objects.filter(title=name_serie)
		if len(serie) < 1:
			return HttpResponseRedirect('http://localhost:8000/random/?serie_name='+name_serie)
		serie = serie[0]
		n_season = randint(0, len(serie.seasons)-1)
		season = serie.seasons[n_season]
		n_season = season.season_number
		n_ep = randint(0, len(season.episodes)-1)
		ep = season.episodes[n_ep]
		n_ep = ep.ep_number
		ret = {
			'title': ep.title,
			'season': n_season,
			'ep': n_ep,
			'spoiler': ep.description,
			'awards': ep.awards,
			'grade': ep.awards,
			'year': ep.year,
			'time': ep.duration,
			'poster': serie.poster,
			'more': ep.imdb_id,
			'netflixId': ep.netflix_id,
			'Response': True
		}
		return HttpResponse(json.dumps(ret), content_type=content_type)

@require_http_methods(['GET'])
def v_random_ep(request):
	content_type = "application/json; charset=utf-8; encoding=utf-8"
	if 'serie_name' in request.GET:
		serie_name = request.GET['serie_name'].upper()
		if not serie_name in special_series.keys():
			try:
				data = fetch_num_seasons(serie_name)
				num_seasons = data['num_seasons']
				poster = data['poster']
			except:
				return HttpResponse(json.dumps({'Response': 'False', 'error': 'Série não encontrada!', 'status': '404' }), content_type=content_type)
		else:
			num_seasons = special_series[serie_name]['num_seasons']
			poster = special_series[serie_name]['poster']
		selected_season = random_number(1, num_seasons)
		num_eps = fetch_num_eps(serie_name, selected_season)
		selected_ep = random_number(1, num_eps)
		ep_info = fetch_ep_info(serie_name, selected_season, selected_ep)
		#ep_info['spoiler'] = translate(ep_info['spoiler'])
		ep_info['poster'] = poster
		ep_info['Response'] = True
		if serie_name in special_series.keys():
			ep_info['netflixId'] = str(mapEpNum(serie_name, selected_season-1, selected_ep))
		else:
			ep_info['netflixId'] = ''
		return HttpResponse(json.dumps(ep_info), content_type=content_type)
	return HttpResponse(json.dumps({'Response': False, 'error': 'Nome da série em branco!', 'status': '400' }), content_type=content_type)

