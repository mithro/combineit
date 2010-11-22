#!/usr/bin/python2.5
#

"""This module represents what people have voted for."""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.1')

import pprint
import logging
import re

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import json

import django_extra

from models.base import *
from models.peruser import *



class PopulatePage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return

    game = Game(name='test', owner=user, key_name='testgame1')
    game.put()

    for i in range(0, 3):
      cat = Category(game=game, name='Category %s'%i, key_name='cat%s'%i)
      cat.put()

      for j in range(0, 3):
        element = Element(
            game=game,
            name='Element %i in Category %i' % (j, i),
            category=cat,
            key_name='element%s%s' % (i,j))
        element.put()

    combine = Combination(
        key_name="comb1",
        game=game,
        inputkeys=['element00', 'element01'],
        outputkeys=['element02'])
    combine.put()


class BasePage(webapp.RequestHandler):
  def setup(self, gameurl):
    # User needs to be logged in
    user = users.get_current_user()
    logging.debug("User %s", user)
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return False

    # Find the game object associated with this page..
    game = Game.all().filter('url =', gameurl).get()
    if not game:
      logging.warn('No game found %s', gameurl)
      return False

    self.user = user
    self.game = game

    return True

  def render(self, tmpl, result):
    output = self.request.get('output')

    if output == 'json':
      self.response.headers['Content-Type'] = 'application/json'

      self.response.out.write(json.JSONEncoder().encode(result))

    elif output == 'text':
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write(pprint.pformat(result))
    else:
      result['game'] = self.game
      result['user'] = self.user

      self.response.headers['Content-Type'] = 'text/html'
      self.response.out.write(template.render(tmpl, result))

###############################################################################
###############################################################################

class DeletePage(BasePage):
  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    key = self.request.get('key')
    object = self.klass.get(key)
    object.delete()
    self.redirect('/%s/%s/list' % (self.game.url, self.url))

class ElementDeletePage(DeletePage):
  url = "elements"
  klass = Element


class CategoryDeletePage(DeletePage):
  url = "categories"
  klass = Category

###############################################################################
###############################################################################

class EditListPage(BasePage):
  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    logging.debug('EditListPage for %s', self.klass)

    query = self.klass.all()
    query.filter('game =', self.game)

    objects = [i for i in query.fetch(1000)]

    logging.warn(objects)

    self.render('templates/edit-list.html', 
                {'objects': objects, 'url': self.url})


class ElementListPage(EditListPage):
  url = "elements"
  klass = Element


class CategoryListPage(EditListPage):
  url = "categories"
  klass = Category

###############################################################################
###############################################################################

class EditPage(BasePage):

  def common(self, gameurl):
    if not self.setup(gameurl):
      return

    key = self.request.get('key')
    if key:
      object = self.klass.get(key)
    else:
      object = self.klass(game=self.game, name='Name goes here',
                          description='Description goes here.')

    for attr in "name", "description", "icon":
      attr_value = self.request.get(attr).strip()
      if attr_value:
        setattr(object, attr, attr_value)

    return object

  def get(self, gameurl):
    object = self.common(gameurl)
    if not object:
      return

    self.render(object)


class ElementEditPage(EditPage):
  url = "elements"
  klass = Element

  def post(self, gameurl):
    element = self.common(gameurl)
    element.category = Category.get(self.request.get('category'))
    element.put()

    self.render(element)

  def render(self, element):
    query = Category.all()
    query.filter('game =', self.game)
    categories = query.fetch(1000)

    EditPage.render(self, 'templates/edit-element.html',
                    {'object': element,
                     'categories': categories})


class CategoryEditPage(EditPage):
  url = "categories"
  klass = Category

  def post(self, gameurl):
    category = self.common(gameurl)
    category.put()

    self.render(category)

  def render(self, category):
    EditPage.render(self, 'templates/edit-category.html',
                    {'object': category})

###############################################################################
###############################################################################

class GamePage(BasePage):
  def setup(self):
    # User needs to be logged in
    user = users.get_current_user()
    logging.debug("User %s", user)
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return False

    self.user = user
    self.game = None
    return True


class GameEditPage(GamePage):

  def common(self):
    if not self.setup():
      return

    # Find the game object with the given URL and check that it's not already
    # used.
    url = self.request.get('url').strip()
    url = re.sub('[^a-zA-Z]', '-', url)

    result = Game.all().filter('url =', url).get()
    if result:
      if str(result.key()) != self.request.get('key'):
        raise ValueError('URL is already in us, pick another url.')

    key = self.request.get('key')
    if key:
      game = Game.get(self.request.get('key'))
    else:
      game = Game(name='Name goes here',
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
      query = Category.all()
      query.filter('game =', game)
      categories = query.fetch(1000)

      query = Element.all()
      query.filter('game =', game)
      elements = query.fetch(1000)
    except db.NotSavedError, e:
      categories = []
      elements = []

    BasePage.render(
       self, 'templates/edit-game.html',
       {'object': game, 'categories': categories, 'elements': elements})


class GameEditRedirect(webapp.RequestHandler):
  def get(self, gameurl):
    self.redirect('/game/edit?key=%s' % self.request.get('key'))

class GameDeletePage(GamePage):
  def get(self):
    if not self.setup():
      return

    key = self.request.get('key')
    object = Game.get(key)
    object.delete()
    self.redirect('/')


###############################################################################
###############################################################################

class ElementPage(BasePage):
  """Get a list of elements for a user."""
  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    query = UsersElement.all()
    query.filter('user =', self.user)
    query.filter('game =', self.game)

    return self.render('templates/list.html', {
        'results': [i.reference for i in query.fetch(1000)]})


class CategoryPage(BasePage):
  """Get a list of categories for a user."""
  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    query = UsersCategory.all()
    query.filter('user =', self.user)
    query.filter('game =', self.game)

    return self.render('templates/list.html', {
        'results': [i.reference for i in query.fetch(1000)]})


class CombinePage(BasePage):
  """This page actually does all the work, it takes a list of elements to
  combind and returns if the combination is successful.

  It also returns if any of the elements or categories are new.
  """
  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    input = self.request.getall('to')
    input = list(sorted(input))
    logging.debug('input %s', input)

    query = Combination.all()
    for element in input:
      query.filter('inputkeys =', element)

    results = query.fetch(1000)
    logging.debug('results %s', results)

    if not results:
      self.render('templates/nocombine.html', {'code': 404, 'error': 'No dice!'})
      return

    for combination in results:
      # Check the match is exact
      tomatch = []
      for elementid in combination.inputkeys:
        tomatch.append(elementid)
      tomatch = list(sorted(tomatch))

      if input == tomatch:
        break
    else:
      self.render('templates/nocombine.html', {'code': 302, 'error': 'Almost!'})
      return

    categories = set()
    new_elements = set()
    for element in combination.output:
      categories.add(element.category)

      if UsersElement.Create(self.user, self.game, element):
        new_elements.add(element)

    new_categories = set()
    for category in categories:
      if UsersCategory.Create(self.user, self.game, category):
        new_categories.add(category)

    return self.render(
        'templates/combine.html',
        {'code': 200,
         'combination': combination,
         'new_elements': new_elements,
         'new_categories': new_categories})


class IndexPage(webapp.RequestHandler):
  def get(self):
    query = Game.all()
    games = [i for i in query.fetch(1000)]

    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(template.render(
      'templates/index.html', {'games': games}))


class PlayPage(BasePage):
  def post(self, gameurl):
    if not self.setup(gameurl):
      return

    tocombined = UsersElement.get(self.request.get_all('tocombined'))

    categories_query = UsersCategory.all()
    categories_query.filter('game =', self.game)
    categories_query.filter('user =', self.user)
    categories = categories_query.fetch(1000)

    # Populate the database
    if not categories:
      for category_key in self.game.starting_categories:
        category = Category.get(category_key)

        categories.append(
            UsersCategory.Create(self.user, self.game, category))

      for element_key in self.game.starting_elements:
        element = Element.get(element_key)
        UsersElement.Create(self.user, self.game, element)

    category_id = self.request.get('category')
    if category_id:
      category = Category.get(category_id)
      assert category is not None
    else:
      category = categories[0].reference

    elements_query = UsersElement.all()
    elements_query.filter('game =', self.game)
    elements_query.filter('user =', self.user)
    elements_query.filter('category =', category)
    elements = elements_query.fetch(1000)

    return self.render('templates/play.html', {
        'tocombined': tocombined,
        'elements': elements,
        'category': category,
        'categories': categories,
        })

  get = post

class AbandonPage(BasePage):
  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    categories_query = UsersCategory.all(keys_only=True)
    categories_query.filter('game =', self.game)
    categories_query.filter('user =', self.user)
    db.delete(categories_query.fetch(1000))

    elements_query = UsersElement.all(keys_only=True)
    elements_query.filter('game =', self.game)
    elements_query.filter('user =', self.user)
    db.delete(elements_query.fetch(1000))

    self.redirect('/')


application = webapp.WSGIApplication(
  [('/',                     IndexPage),
   ('/(.*)/elements',        ElementPage),
   ('/(.*)/elements/list',   ElementListPage),
   ('/(.*)/elements/edit',   ElementEditPage),
   ('/(.*)/elements/delete', ElementDeletePage),
   ('/(.*)/categories',      CategoryPage),
   ('/(.*)/categories/list', CategoryListPage),
   ('/(.*)/categories/edit', CategoryEditPage),
   ('/(.*)/categories/delete', CategoryDeletePage),
   ('/(.*)/combine',         CombinePage),
   ('/(.*)/play',            PlayPage),
   ('/(.*)/abandon',         AbandonPage),
   ('/game/edit',            GameEditPage),
   ('/game/delete',          GameDeletePage),
   ('/(.*)/edit',            GameEditRedirect),
   ('/populate',             PopulatePage),
   ],
  debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
