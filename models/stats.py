
from google.appengine.ext import db

import base


class FeaturedGame(db.Model):
  reference = db.ReferenceProperty(base.Game)
