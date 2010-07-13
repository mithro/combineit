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
    query = Game.all()
    query.filter('name =', gamekey)
    games = query.fetch(1)
    logging.debug("Games %s", games)
    if not games:
      return False

    self.user = user
    self.game = games[0]

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


def EditPage(item):
  class EditPage(BasePage):
    def setup(self, gamekey):
      if not BasePage.setup(self, gamekey):
         return

      self.key_name = self.request.get('key_name')
      if self.key_name:
        return item.Meta.model.get_by_key_name(self.key_name)

    def get(self, gamekey):
      entity = self.setup(gamekey)
      self.render('templates/form.html', 
                  {'key_name': self.key_name,
                   'form': item(instance=entity)})
  
    def post(self, gamekey):
      entity = self.setup(gamekey)
 
      data = item(data=self.request.POST, instance=entity)
      if data.is_valid():
        entity = data.save(commit=False)
        entity.game = self.game
        entity.user = self.user
        entity.put()
        self.redirect('')
      else:
        self.render('templates/form.html', 
                    {'key_name': self.key_name,
                     'form': data})

  return EditPage

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

from forms import base

application = webapp.WSGIApplication(
  [('/(.*)/elements',        ElementPage),
   ('/(.*)/elements/edit',   EditPage(base.ElementForm)),
   ('/(.*)/categories',      CategoryPage),
   ('/(.*)/categories/edit', EditPage(base.CategoryForm)),
   ('/(.*)/combine',         CombinePage),
   ('/(.*)/combine/edit',    EditPage(base.CombinationForm)), 
   ('/populate',             PopulatePage),
   ],
  debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
