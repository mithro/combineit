# Copyright (c) 2010 Google Inc. All rights reserved.
# Use of this source code is governed by a Apache-style license that can be
# found in the LICENSE file.

from google.appengine.ext import db

import base


class FeaturedGame(db.Model):
  reference = db.ReferenceProperty(base.Game)

class PopularGame(db.Model):
  reference = db.ReferenceProperty(base.Game)
