#!/usr/bin/python2.5
#

"""Describe a game."""

from google.appengine.ext import db


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
  category = db.ReferenceProperty(Category)


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
