import json
from os import listdir
from os.path import isfile, join, realpath, dirname
from models import Episode, Season, Serie

def getSerieInfo(file_path):
	try:
		file = open((file_path), 'r')
		data = json.loads(file.read())
		file.close()
		if data["video"]["type"] != "show":
			return False
		ret_json = {
			'serie_name': data['video']['title'].upper(),
			'seasons': data['video']['seasons']
		}
		return ret_json
	except (IOError, KeyError, ValueError) as e:
		return False


#dirpath = join(dirname(realpath(__file__)), 'series')
#series = [f for f in listdir(dirpath) if isfile(join(dirpath, f))]

#for i in xrange(0, len(series)):

#print counting
#print len(series)