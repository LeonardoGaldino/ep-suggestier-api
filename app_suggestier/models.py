from django.db import models

from djangotoolbox.fields import ListField, EmbeddedModelField

class Episode(models.Model):
	title = models.CharField(max_length=100)
	ep_number = models.CharField(max_length=10)
	description = models.CharField(max_length=2000)
	grade = models.CharField(max_length=10)
	year = models.CharField(max_length=10)
	awards = models.CharField(max_length=300)
	duration = models.CharField(max_length=10)
	netflix_id = models.CharField(max_length=20)
	imdb_id = models.CharField(max_length=150)

class Season(models.Model):
	season_number = models.CharField(max_length=5)
	episodes = ListField(EmbeddedModelField('Episode'))

class Serie(models.Model):
	title = models.CharField(max_length=100)
	poster = models.CharField(max_length=300)
	seasons = ListField(EmbeddedModelField('Season'))

