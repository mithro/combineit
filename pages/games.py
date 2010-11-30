# Copyright (c) 2010 Google Inc. All rights reserved.
# Use of this source code is governed by a Apache-style license that can be
# found in the LICENSE file.

"""Module for all things dealing with Games."""

import re

from google.appengine.ext import db
from google.appengine.ext import webapp

import common
from models import base


class GamePage(common.LoginPage):
  def setup(self):
    common.LoginPage.setup(self, '')
    return bool(self.user)


class GameEditPage(GamePage):
  title = 'Edit Game'

  def common(self):
    if not self.setup():
      return

    # Find the game object with the given URL and check that it's not already
    # used.
    url = self.request.get('url').strip()
    url = re.sub('[^a-zA-Z]', '-', url)

    result = base.Game.all().filter('url =', url).get()
    if result:
      if str(result.key()) != self.request.get('key'):
        raise ValueError('URL is already in us, pick another url.')

    key = self.request.get('key')
    if key:
      game = base.Game.get(self.request.get('key'))
    else:
      game = base.Game(name='Name goes here',
                  description='Description goes here.',
                  url='newurl')

    if url:
      game.url = url

    for attr in "name", "description", "icon":
      attr_value = self.request.get(attr).strip()
      if attr_value:
        setattr(game, attr, attr_value)

    starting_categories = self.request.get_all('starting_categories')
    if starting_categories:
      game.starting_categories = starting_categories

    starting_elements = self.request.get_all('starting_elements')
    if starting_elements:
      game.starting_elements = starting_elements

    return game

  def get(self):
    game = self.common()
    if not game:
      return

    self.render(game)

  def post(self):
    game = self.common()
    if not game:
      return

    game.put()
    self.render(game)

  def render(self, game):
    try:
      query = base.Category.all()
      query.filter('game =', game)
      categories = query.fetch(1000)

      query = base.Element.all()
      query.filter('game =', game)
      elements = query.fetch(1000)
    except db.NotSavedError, e:
      categories = []
      elements = []

    common.LoginPage.render(
        self, 'templates/edit-game.html',
        {'object': game,
         'categories': categories,
         'elements': elements})


class GameDeletePage(GamePage):
  def get(self):
    if not self.setup():
      return

    key = self.request.get('key')
    object = base.Game.get(key)
    object.delete()
    self.redirect('/')


class GameEditRedirect(webapp.RequestHandler):
  def get(self, gameurl):
    self.redirect('/games/edit?key=%s' % self.request.get('key'))
