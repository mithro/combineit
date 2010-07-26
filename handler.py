#!/usr/bin/python2.5
#

"""This module represents what people have voted for."""


import pprint
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import json

from google.appengine.ext import db
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
        game=game, inputkeys=['element00', 'element01'], outputkeys=['element02'])
    combine.put()


class BasePage(webapp.RequestHandler):
  def setup(self, gamekey):
    # User needs to be logged in
    user = users.get_current_user()
    logging.debug("User %s", user)
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return False

    # Find the game object associated with this page..
    game = Game.get_by_key_name(gamekey)
    if not game:
      logging.warn('No game found %s', gamekey)
      return False
    game.key_name = gamekey

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

class DeletePage(BasePage):
  def get(self, gamekey):
    if not self.setup(gamekey):
      return

    key = self.request.get('key')
    object = self.klass.get(key)
    object.delete()
    self.redirect('/%s/%s/list' % (self.game.key().name(), self.url))

class ElementDeletePage(DeletePage):
  url = "elements"
  klass = Element


class CategoryDeletePage(DeletePage):
  url = "categories"
  klass = Category


class EditListPage(BasePage):
  def get(self, gamekey):
    if not self.setup(gamekey):
      return

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


class EditPage(BasePage):

  def get(self, gamekey):
    if not self.setup(gamekey):
      return

    key = self.request.get('key')
    try:
      object = self.klass.get(key)
    except db.BadKeyError:
      object = None

    self.render(object)

  def post(self, gamekey):
    if not self.setup(gamekey):
      return

    try:
      object = self.klass.get(self.request.get('key'))
    except db.BadKeyError:
      object = self.klass(game=self.game, name='New', desc='New')

    for attr in "name", "description", "icon":
      setattr(object, attr, self.request.get(attr))

    return object

class ElementEditPage(EditPage):
  url = "elements"
  klass = Element

  def post(self, gamekey):
    element = EditPage.post(self, gamekey)
    element.category = Category.get(self.request.get('category'))
    element.key = element.put()

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

  def post(self, gamekey):
    category = EditPage.post(self, gamekey)
    category.put()

    self.render(category)

  def render(self, category):
    EditPage.render(self, 'templates/edit-category.html', 
                    {'object': category})


class ElementPage(BasePage):
  """Get a list of elements for a user."""
  def get(self, gamekey):
    if not self.setup(gamekey):
      return

    query = UsersElement.all()
    query.filter('user =', self.user)
    query.filter('game =', self.game)

    return self.render('templates/list.html', {
        'results': [i.reference for i in query.fetch(1000)]})


class CategoryPage(BasePage):
  """Get a list of categories for a user."""
  def get(self, gamekey):
    if not self.setup(gamekey):
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
  def get(self, gamekey):
    if not self.setup(gamekey):
      return

    input = self.request.get('to').split(',')
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

application = webapp.WSGIApplication(
  [('/(.*)/elements',        ElementPage),
   ('/(.*)/elements/list',   ElementListPage),
   ('/(.*)/elements/edit',   ElementEditPage),
   ('/(.*)/elements/delete', ElementDeletePage),
   ('/(.*)/categories',      CategoryPage),
   ('/(.*)/categories/list', CategoryListPage),
   ('/(.*)/categories/edit', CategoryEditPage),
   ('/(.*)/categories/delete', CategoryDeletePage),
   ('/(.*)/combine',         CombinePage),
   ('/populate',             PopulatePage),
   ],
  debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
