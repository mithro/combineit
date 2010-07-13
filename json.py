
from google.appengine.ext import db
from django.utils import simplejson

class JSONEncoder(simplejson.JSONEncoder):
  """JSON encoder which handles db.Model objects."""
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
