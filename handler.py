#!/usr/bin/python2.5
#

"""This module represents what people have voted for."""


import pprint
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from django.utils import simplejson


# The following tables describe a game.

class Game(db.Model):
  """A single combination game."""
  name = db.StringProperty(required=True)
  description = db.StringProperty(multiline=True)
  background = db.StringProperty()
  owner = db.UserProperty(required=True)

class Category(db.Model):
  """How to group different elements together."""
  game = db.ReferenceProperty(Game, required=True)
  name = db.StringProperty(required=True)
  description = db.StringProperty(multiline=True)
  icon = db.StringProperty()

class Element(db.Model):
  """Fundamental building blocks of the game.

  Each element can be in only one category.
  """
  game = db.ReferenceProperty(Game, required=True)
  name = db.StringProperty(required=True)
  description = db.StringProperty(multiline=True)
  icon = db.StringProperty()
  category = db.ReferenceProperty(Category, required=True)

class Combination(db.Model):
  """The actual point of the game, to combined elements together to produce more
  elements.
  """
  game = db.ReferenceProperty(Game, required=True)
  name = db.StringProperty()
  description = db.StringProperty(multiline=True)

  inputkeys = db.StringListProperty()
  outputkeys = db.StringListProperty()

  @property
  def input(self):
    for key in self.inputkeys:
      yield Element.get_by_key_name(key)

  @property
  def output(self):
    for key in self.outputkeys:
      yield Element.get_by_key_name(key)


# The following tables describe the "state" of a person who is playing a game.


class Reference(db.Model):
  @classmethod
  def Create(cls, user, game, reference):
    """Returns if a new object was created."""
    key_name = '%s--%s--%s' % (user.user_id(), game.key(), reference.key())

    if cls.get_by_key_name(key_name):
      return False

    obj = cls(user=user, game=game, reference=reference, key_name=key_name)
    obj.put()
    return obj

  user = db.UserProperty()
  game = db.ReferenceProperty(Game)

class UsersElement(Reference):
  """The list of elements a User has discovered."""
  reference = db.ReferenceProperty(Element)

class UsersCategory(Reference):
  """The list of categories a user has discovered."""
  reference = db.ReferenceProperty(Category)

class UsersCombination(Reference):
  """The list of combinations a User has discovered."""
  reference = db.ReferenceProperty(Combination)


# The actual pages...


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


class JSONEncoder(simplejson.JSONEncoder):
  def default(self, o):
    if isinstance(o, set):
      return list(o)

    try:
      output = {'__type': o.__class__.__name__}
      for property in o.properties():
        cls = getattr(o.__class__, property)
        value = getattr(o, property)

        if isinstance(cls, db.ReferenceProperty):
          value = str(value.key().name())
        elif isinstance(cls, db.UserProperty):
          value = value.user_id()

        output[property] = value
      return output
    except AttributeError:
      return simplejson.JSONEncoder.default(self, o)


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

      self.response.out.write(JSONEncoder().encode(result))

    elif output == 'text':
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write(pprint.pformat(result))
    else:
      result['game'] = self.game
      result['user'] = self.user

      self.response.headers['Content-Type'] = 'text/html'
      self.response.out.write(template.render(tmpl, result))


class ElementPage(BasePage):
  """Get a list of elements for a user."""
  def get(self, gamekey):
    if not self.setup(gamekey):
      return

    query = UsersElement.all()
    query.filter('user =', self.user)
    query.filter('game =', self.game)

    return self.render('list.html', {
        'results': [i.reference for i in query.fetch(1000)]})


class CategoryPage(BasePage):
  """Get a list of categories for a user."""
  def get(self, gamekey):
    if not self.setup(gamekey):
      return

    query = UsersCategory.all()
    query.filter('user =', self.user)
    query.filter('game =', self.game)

    return self.render('list.html', {
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
      self.render('nocombine.html', {'code': 404, 'error': 'No dice!'})
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
      self.render('nocombine.html', {'code': 302, 'error': 'Almost!'})
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
        'combine.html',
        {'code': 200,
         'combination': combination,
         'new_elements': new_elements,
         'new_categories': new_categories})


application = webapp.WSGIApplication(
  [('/(.*)/elements',   ElementPage),
   ('/(.*)/categories', CategoryPage),
   ('/(.*)/combine',    CombinePage),
   ('/populate',        PopulatePage),
   ],
  debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
