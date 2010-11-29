
from google.appengine.ext import db
from django.template.defaultfilters import stringfilter, register
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


@register.filter
def key(obj):
  if not obj:
    return ''

  try:
    key = str(obj.key())
    return key
  except db.NotSavedError, e:
    return ''


@register.filter
def icon(obj, autoescape=False):
  if not obj:
    return ''

  if autoescape:
    esc = conditional_escape
  else:
    esc = lambda x: x

  if hasattr(obj, 'reference'):
     realobj = obj.reference
  else:
     realobj = obj

  return mark_safe("""\
<div class='icon'>
  <span>%(name)s</span>
  <img src='%(icon)s' alt='%(desc)s'>
</div>
""" % {'icon': esc(realobj.icon),
       'desc': esc(realobj.description),
       'name': esc(realobj.name)})

icon.needs_autoescape = True
