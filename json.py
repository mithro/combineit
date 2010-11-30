# Copyright (c) 2010 Google Inc. All rights reserved.
# Use of this source code is governed by a Apache-style license that can be
# found in the LICENSE file.

import datetime

from google.appengine.ext import db
from django.utils import simplejson

from models import peruser

class JSONEncoder(simplejson.JSONEncoder):
  """JSON encoder which handles db.Model objects."""
  ignore = ('created_by', 'created_on',
            'updated_by', 'updated_on',
            'game', 'user')

  def default(self, o, nokey=False):
    if isinstance(o, set):
      return list(o)

    try:
      output = {'__type': o.__class__.__name__,
                'key': str(o.key())}

      for property in o.properties():
        if property in self.ignore:
          continue

        cls = getattr(o.__class__, property)
        value = getattr(o, property)

        # FIXME: Hack to stop multiple output of categories for UsersElements
        if isinstance(value, peruser.UsersElement):
          if property == 'category':
            continue

        if isinstance(cls, db.ReferenceProperty):
          value = self.default(value)
        elif isinstance(cls, db.UserProperty):
          value = value.user_id()

        if isinstance(value, datetime.datetime):
          value = str(value)

        output[property] = value
      return output
    except AttributeError:
      return simplejson.JSONEncoder.default(self, o)
