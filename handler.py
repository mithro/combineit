#!/usr/bin/python2.5
#

"""This module represents what people have voted for."""

import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

# The following tables describe a game.

class Game(db.Model):
  """A single combination game."""
  name = db.StringProperty()
  description = db.StringProperty(multiline=True)
  background = db.StringProperty()
  owner = db.UserProperty()

class Category(db.Model):
  """How to group different elements together."""
  game = db.ReferenceProperty(Game)
  name = db.StringProperty()
  description = db.StringProperty(multiline=True)
  icon = db.StringProperty()

class Element(db.Model):
  """Fundamental building blocks of the game.

  Each element can be in only one category.
  """
  game = db.ReferenceProperty(Game)
  name = db.StringProperty()
  description = db.StringProperty(multiline=True)
  icon = db.StringProperty()
  category = db.ReferenceProperty(Category)

class Combination(db.Model):
  """The actual point of the game, to combined elements together to produce more
  elements.
  """
  game = db.ReferenceProperty(Game)
  name = db.StringProperty()
  description = db.StringProperty(multiline=True)

  input = db.StringListProperty()
  output = db.StringListProperty()

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
        game=game, input=['element00', 'element01'], output=['element02'])
    combine.put()


class BasePage(webapp.RequestHandler):
  def setup(self, game):
    # User needs to be logged in
    user = users.get_current_user()
    logging.debug("User %s", user)
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
      return (None, None)

    # Find the game object associated with this page..
    query = Game.all()
    query.filter('name =', game)
    games = query.fetch(1)
    logging.debug("Games %s", games)
    if not games:
      return (None, None)

    return (user, games[0])

  def render(self, result):
    import pprint
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write(pprint.pformat(result))


class ElementPage(BasePage):
  """Get a list of elements for a user."""
  def get(self, game):
    user, game = self.setup(game)
    if not user or not game:
      return

    query = UsersElement.all()
    query.filter('user =', user)
    query.filter('game =', game)

    return self.render({'results': [i.reference.name for i in query.fetch(1000)]})


class CategoryPage(BasePage):
  """Get a list of categories for a user."""
  def get(self, game):
    user, game = self.setup(game)
    if not user or not game:
      return

    query = UsersCategory.all()
    query.filter('user =', user)
    query.filter('game =', game)

    return self.render({'results': [i.reference.name for i in query.fetch(1000)]})


class CombinePage(BasePage):
  """This page actually does all the work, it takes a list of elements to
  combind and returns if the combination is successful.

  It also returns if any of the elements or categories are new.
  """
  def get(self, game):
    user, game = self.setup(game)
    if not user or not game:
      return

    input = self.request.get('to').split(',')
    input = list(sorted(input))
    logging.debug('input %s', input)

    query = Combination.all()
    for element in input:
      query.filter('input =', element)

    results = query.fetch(1000)
    logging.debug('results %s', results)

    if not results:
      self.render('No dice!')
      return

    for combination in results:
      # Check the match is exact
      tomatch = []
      for elementid in combination.input:
        tomatch.append(elementid)
      tomatch = list(sorted(tomatch))

      if input == tomatch:
        break
    else:
      self.render('Almost!')
      return

    categories = set()
    new_elements = set()
    for elementid in combination.output:

      element = Element.get_by_key_name(elementid)
      if not element:
        raise Exception('Element %s not found' % element)

      categories.add(element.category)

      if UsersElement.Create(user, game, element):
        new_elements.add(element)

    new_categories = set()
    for category in categories:
      if UsersCategory.Create(user, game, category):
        new_categories.add(category)

    return self.render({'combination': combination,
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
