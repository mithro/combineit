
from google.appengine.ext import db
from django.template.defaultfilters import stringfilter, register

@register.filter
def key(obj):

  if not obj:
    return ''

  try:
    key = str(obj.key())
    return key
  except db.NotSavedError, e:
    return ''
