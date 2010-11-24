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
import urlparse

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from django.utils.safestring import mark_safe
import django_extra

import json

from models.base import *
from models.peruser import *
from models.stats import *


class BasePage(webapp.RequestHandler):
  title = ''

  def setup(self, gameurl):
    self.game = None

    # User needs to be logged in
    self.user = users.get_current_user()

    # Find the game object associated with this page..
    self.game = Game.all().filter('url =', gameurl).get()
    if not self.game:
      return False

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
      logging.info('url %s', urlparse.urlparse(self.request.uri).path)


      result.update({
          'title': self.title,
          'path': urlparse.urlparse(self.request.uri).path,
          'login_url': users.create_login_url(self.request.uri),
          'logout_url': users.create_logout_url(self.request.uri),
          'game': self.game,
          'user': self.user,
          'is_current_user_admin': users.is_current_user_admin(),
          'featured_games': FeaturedGame.all().fetch(10),
          'top_games': [],
          })

      self.response.headers['Content-Type'] = 'text/html; charset=utf-8'
      self.response.out.write(template.render(tmpl, result))

  def RenderBench(self, prefix, thisform, submitform=None, default_elements=[]):
    # FIXME: This doesn't belong on this class

    # Get all the elements in the current "scratch area"
    keys = self.request.get_all('%s_scratch' % prefix)
    if not keys:
      keys = default_elements

    logging.info('key starting %r', keys)
    try:
      toremove = int(self.request.get('%s_remove' % prefix))
      logging.info('key toremove %r', toremove)
      del keys[toremove]
    except ValueError:
      pass

    toadd = self.request.get('%s_add' % prefix)
    if toadd:
      logging.info('key toadd %r', toadd)
      keys.append(toadd)

    logging.info('keys final %r', keys)

    scratch = Element.get(keys)

    # Work out which category is currently display on the bench.
    query = Category.all()
    query.filter('game =', self.game)
    categories = query.fetch(1000)

    selected_category_key = self.request.get(prefix+'_category')
    try:
      selected_category = Category.get(selected_category_key)
    except db.BadKeyError, e:
      selected_category = categories[0]

    query = Element.all()
    query.filter('game =', self.game)
    query.filter('category =', selected_category)
    elements = query.fetch(1000)

    if not submitform:
      submitform = thisform

    # Render out the bench
    html = template.render(
        'templates/bench-admin.html',
        {'submitform': submitform,
         'thisform': thisform,
         'scratch': scratch,
         'categories': categories,
         'elements': elements,
         'selected_category': selected_category,
         'prefix': prefix})

    return mark_safe(html), scratch


class LoginPage(BasePage):
  def setup(self, gameurl):
    result = BasePage.setup(self, gameurl)

    if self.user is None:
      self.redirect(users.create_login_url(self.request.uri))
      return False

    return result


###############################################################################
###############################################################################


class IndexPage(BasePage):
  def get(self):
    self.setup('')

    query = Game.all()
    games = [i for i in query.fetch(1000)]

    self.render(
        'templates/index.html', {'games': games})


###############################################################################
###############################################################################

class DeletePage(LoginPage):
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


class ComboDeletePage(DeletePage):
  url = "combos"
  klass = Combination


###############################################################################
###############################################################################

class EditListPage(LoginPage):
  title = 'Edit List'

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


class ComboListPage(EditListPage):
  url = "combos"
  klass = Combination


###############################################################################
###############################################################################

class EditPage(LoginPage):
  title = 'Edit'
  fields = ("name", "description", "icon")

  def common(self, gameurl):
    if not self.setup(gameurl):
      return

    key = self.request.get('key')
    if key:
      object = self.klass.get(key)
    else:
      object = self.klass(game=self.game)

    for attr in self.fields:
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




class ComboEditPage(EditPage):
  url = "combo"
  klass = Combination
  fields = ("name", "description")

  def post(self, gameurl):
    combo = self.common(gameurl)
    if not combo:
      return

    self.render(combo)

    # Quick Create doesn't set this..
    if self.request.get('action') == 'Save':
      combo.put()

  def render(self, combo):
    input_html, input_elements = self.RenderBench(
        'input', thisform='edit', default_elements=combo.inputkeys)
    if input_elements:
      combo.inputkeys = [str(x.key()) for x in input_elements]

    output_html, output_elements = self.RenderBench(
        'output', thisform='edit', default_elements=combo.outputkeys)
    if output_elements:
      combo.outputkeys = [str(x.key()) for x in output_elements]

    EditPage.render(self, 'templates/edit-combo.html',
                    {'object': combo,
                     'input_bench': input_html,
                     'output_bench': output_html})

###############################################################################
###############################################################################

class GamePage(LoginPage):
  def setup(self):
    LoginPage.setup(self, '')
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

    LoginPage.render(
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

class ElementPage(LoginPage):
  """Get a list of elements for a user."""
  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    query = UsersElement.all()
    query.filter('user =', self.user)
    query.filter('game =', self.game)

    return self.render('templates/list.html', {
        'results': [i.reference for i in query.fetch(1000)]})


class CategoryPage(LoginPage):
  """Get a list of categories for a user."""
  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    query = UsersCategory.all()
    query.filter('user =', self.user)
    query.filter('game =', self.game)

    return self.render('templates/list.html', {
        'results': [i.reference for i in query.fetch(1000)]})


class CombinePage(LoginPage):
  """This page actually does all the work, it takes a list of elements to
  combind and returns if the combination is successful.

  It also returns if any of the elements or categories are new.
  """
  def post(self, gameurl):
    if not self.setup(gameurl):
      return

    input = self.request.get_all('tocombined')
    input = list(sorted(input))
    logging.debug('input %s', input)
    if not input:
      self.render('templates/nocombine.html', {'code': 404, 'error': 'No input!'})
      return

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
    for element in combination.output():
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


class PlayPage(LoginPage):
  def post(self, gameurl):
    if not self.setup(gameurl):
      return

    scratch_html, elements = self.RenderBench('scratch', thisform='scratch', submitform='bench')
    return self.render('templates/play.html', {
        'scratch': elements,
        'scratch_bench': scratch_html,
        })

  get = post

class AbandonPage(LoginPage):
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
   ('/(.*)/combos/list',     ComboListPage),
   ('/(.*)/combos/edit',     ComboEditPage),
   ('/(.*)/combos/delete',   ComboDeletePage),
   ('/(.*)/combine',         CombinePage),
   ('/(.*)/play',            PlayPage),
   ('/(.*)/abandon',         AbandonPage),
   ('/game/edit',            GameEditPage),
   ('/game/delete',          GameDeletePage),
   ('/(.*)/edit',            GameEditRedirect),
   ],
  debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
