#!/usr/bin/python2.5
#

"""Describe the "state" of a person who is playing a game."""

from google.appengine.ext import db

from base import *

class Reference(db.Model):
  """Model which references another model."""

  @classmethod
  def CreateExtra(cls, user, game, reference):
    return {}

  @classmethod
  def Create(cls, user, game, reference):
    """Returns if a new object was created."""
    key_name = '%s--%s--%s' % (user.user_id(), game.key(), reference.key())

    if cls.get_by_key_name(key_name):
      return False

    args = dict(user=user, game=game, reference=reference, key_name=key_name)
    args.update(cls.CreateExtra(user, game, reference))

    obj = cls(**args)
    obj.put()
    return obj

  user = db.UserProperty()
  game = db.ReferenceProperty(Game)


class UsersElement(Reference):
  """The list of elements a User has discovered."""

  @classmethod
  def CreateExtra(cls, user, game, reference):
    return dict(category=reference.category)

  reference = db.ReferenceProperty(Element)
  category = db.ReferenceProperty(Category)


class UsersCategory(Reference):
  """The list of categories a user has discovered."""

  reference = db.ReferenceProperty(Category)


class UsersCombination(Reference):
  """The list of combinations a User has discovered."""

  reference = db.ReferenceProperty(Combination)
