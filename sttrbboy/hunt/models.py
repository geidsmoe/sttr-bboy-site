# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import datetime

from sttrbboy.overwrite_fs import OverwriteFileSystemStorage
from sttrbboy import settings


def gen_list_filename(instance, fn):
	return "lists/%d%s" % (instance.year, os.path.splitext(fn)[1])


# Create your models here.
class Hunt(models.Model):
	year = models.IntegerField()
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()
	list_pdf = models.FileField(upload_to=gen_list_filename, storage=OverwriteFileSystemStorage(), blank=True)

	def __unicode__(self):
		return str(self.year)

	@property
	def status(self):
		if self.start_date and self.end_date:
			now = timezone.now()
			if self.start_date < now < self.end_date:
				return 'in_progress'
			elif now > self.end_date:
				return 'finished'
			else:
				return 'future'
		else:
			return 'N/A'

	def get_scavvies(self):
		return self.scavvies.all()

	@models.permalink
	def get_absolute_url(self):
		return ('hunt|show', [self.pk])


class Scavvie(models.Model):
	class Meta:
		unique_together = ('user', 'hunt')

	page_captain = models.BooleanField(default=False)
	captain = models.BooleanField(default=False)
	hunt = models.ForeignKey(Hunt, related_name='scavvies')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')

	def __unicode__(self):
		if self.user.profile.name:
			return self.user.profile.name
		else:
			return self.user.first_name + " " + self.user.last_name

	@models.permalink
	def get_absolute_url(self):
		return ('scavvie|show', [self.pk])


class Page(models.Model):
	class Meta:
		unique_together = ('number', 'hunt', 'roadtrip')

	number = models.IntegerField(validators=[MinValueValidator(0)])
	hunt = models.ForeignKey(Hunt, related_name='pages')
	page_captain = models.ForeignKey(Scavvie, blank=True, null=True, related_name='pages')
	olympics = models.BooleanField(default=False)
	roadtrip = models.BooleanField(default=False)

	def __unicode__(self):
		if self.olympics:
			return "Scav Olympics"
		elif self.roadtrip:
			return "Page %d (Road Trip)" % self.number
		else:
			return "Page %d" % self.number

	@models.permalink
	def get_absolute_url(self):
		if self.olympics:
			return ('olympicspage|show', [self.hunt.pk, self.number]) 
		elif self.roadtrip:
			return ('roadtrippage|show', [self.hunt.pk, self.number])
		else:
			return ('page|show', [self.hunt.pk, self.number])


class Tag(models.Model):
	title = models.CharField(max_length=512)

	def __unicode__(self):
		return self.title


class Item(models.Model):
	class Meta:
		unique_together = ('number', 'hunt', 'olympics', 'roadtrip')

	number = models.IntegerField(validators=[MinValueValidator(0)])
	points = models.DecimalField(max_digits=8, decimal_places=5)
	short_desc = models.CharField(max_length=128)
	full_desc = models.TextField(blank=True)
	completed = models.BooleanField(default=False)
	started = models.BooleanField(default=False)
	olympics = models.BooleanField(default=False)
	roadtrip = models.BooleanField(default=False)

	tags = models.ManyToManyField(Tag, related_name='items')
	page = models.ForeignKey(Page, related_name='items')
	hunt = models.ForeignKey(Hunt, related_name='items')
	time = models.DateTimeField(blank=True, null=True)
	page_captain = models.ForeignKey(Scavvie, blank=True, null=True, related_name='captaining_items')
	interested_scavvies = models.ManyToManyField(Scavvie, related_name='interested_items', blank=True)
	working_scavvies = models.ManyToManyField(Scavvie, related_name='working_items', blank=True)
	completed_scavvies = models.ManyToManyField(Scavvie, related_name='completed_items', blank=True)

	def __unicode__(self):
		if self.olympics:
			return "Scav Olympics %d - %s" % (self.number, self.short_desc)
		else:
			return "Item %d - %s" % (self.number, self.short_desc)

	def get_csv_tags(self):
		status = "unclaimed"
		if self.started:
			status = "started"
		elif self.completed:
			status = "completed"
		return 'id_tags:' + ','.join([it.title for it in self.tags.all()]) + "," + status


	@models.permalink
	def get_absolute_url(self):
		if self.olympics:
			return ('olympicsitem|show', [self.hunt.pk, self.number]) 
		elif self.roadtrip:
			return ('roadtripitem|show', [self.hunt.pk, self.number])
		else:
			return ('item|show', [self.hunt.pk, self.number])

class Comment(models.Model):
	text = models.CharField(max_length=512)
	item = models.ForeignKey(Item, related_name='comments')
	scavvie = models.ForeignKey(Scavvie, related_name='comments')

	def __unicode__(self):
		return self.scavvie.user.profile.name + " " + self.text