# Copyright (c) 2010 Google Inc. All rights reserved.
# Use of this source code is governed by a Apache-style license that can be
# found in the LICENSE file.

"""Describe a game."""

from google.appengine.ext import db


class Game(db.Model):
  """A single combination game."""
  created_by = db.UserProperty(required=True, auto_current_user_add=True)
  created_on = db.DateTimeProperty(required=True, auto_now_add=True)
  updated_by = db.UserProperty(required=True, auto_current_user=True)
  updated_on = db.DateTimeProperty(required=True, auto_now=True)

  url = db.StringProperty(required=True)
  name = db.StringProperty(
      required=True, default='Game name goes here')
  description = db.StringProperty(
      multiline=True, default='Game description goes here.')
  background = db.StringProperty()

  owner = db.UserProperty(required=True, auto_current_user_add=True)
  admin = db.StringListProperty()

  icon = db.StringProperty(default="/images/question-green.png")

  starting_categories = db.StringListProperty()
  starting_elements = db.StringListProperty()

  def is_admin(self, user):
    if user is None:
       return False
    if user == self.owner:
       return True
    if user.user_id() in self.admin:
       return True
    return False


class Category(db.Model):
  """How to group different elements together."""
  created_by = db.UserProperty(required=True, auto_current_user_add=True)
  created_on = db.DateTimeProperty(required=True, auto_now_add=True)
  updated_by = db.UserProperty(required=True, auto_current_user=True)
  updated_on = db.DateTimeProperty(required=True, auto_now=True)

  game = db.ReferenceProperty(Game, required=True)
  name = db.StringProperty(
      required=True, default='Category name goes here')
  description = db.StringProperty(
      multiline=True, default='Category description goes here.')

  icon = db.StringProperty(default="/images/question-yellow.png")

  @property
  def key_str(self):
    return str(self.key())

class Element(db.Model):
  """Fundamental building blocks of the game.

  Each element can be in only one category.
  """
  created_by = db.UserProperty(required=True, auto_current_user_add=True)
  created_on = db.DateTimeProperty(required=True, auto_now_add=True)
  updated_by = db.UserProperty(required=True, auto_current_user=True)
  updated_on = db.DateTimeProperty(required=True, auto_now=True)

  game = db.ReferenceProperty(Game, required=True)
  name = db.StringProperty(
      required=True, default='Element name goes here')
  description = db.StringProperty(
      multiline=True, default='Element description goes here.')

  icon = db.StringProperty(default="/images/question-red.png")

  category = db.ReferenceProperty(Category)

  @property
  def key_str(self):
    return str(self.key())

class Combination(db.Model):
  """The actual point of the game, to combined elements together to produce more
  elements.
  """
  created_by = db.UserProperty(required=True, auto_current_user_add=True)
  created_on = db.DateTimeProperty(required=True, auto_now_add=True)
  updated_by = db.UserProperty(required=True, auto_current_user=True)
  updated_on = db.DateTimeProperty(required=True, auto_now=True)

  game = db.ReferenceProperty(Game, required=True)
  name = db.StringProperty(
      required=True, default='Combination name goes here')
  description = db.StringProperty(
      multiline=True, default='Combination description goes here.')

  inputkeys = db.StringListProperty()
  outputkeys = db.StringListProperty()

  def input(self):
    return Element.get(self.inputkeys)

  def output(self):
    return Element.get(self.outputkeys)
