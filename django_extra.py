
import logging

from google.appengine.ext import db
from django.template.defaultfilters import stringfilter, register

@register.filter
def key(obj):

  if not obj:
    logging.info('Django Extra empty -%r', obj)
    return ''

  try:
    key = str(obj.key())
    logging.info('Django Extra %r - %r', key, obj)
    return key
  except db.NotSavedError, e:
    logging.info('Django Extra NotSaved - %r', obj)
    return ''
