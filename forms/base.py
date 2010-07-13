#!/usr/bin/python2.5
#

"""Describe a game."""

from google.appengine.ext.db import djangoforms

from models import base

class GameForm(djangoforms.ModelForm):
  class Meta:
     model = base.Game
     exclude = ['user', 'game']

class CategoryForm(djangoforms.ModelForm):
  class Meta:
     model = base.Category
     exclude = ['user', 'game']


class ElementForm(djangoforms.ModelForm):
  class Meta:
     model = base.Element
     exclude = ['user', 'game']


class CombinationForm(djangoforms.ModelForm):
  class Meta:
     model = base.Combination
     exclude = ['user', 'game']
