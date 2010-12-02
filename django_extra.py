# Copyright (c) 2010 Google Inc. All rights reserved.
# Use of this source code is governed by a Apache-style license that can be
# found in the LICENSE file.

import logging
import re

from google.appengine.ext import db
from django.template.defaultfilters import stringfilter, register
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


@register.filter
def fancy(text, autoescape=False):
  if autoescape:
    esc = conditional_escape
  else:
    esc = lambda x: x

  text = esc(text)

  text = re.sub('\^\{(.*?)\}', r'<sup>\1</sup>', text)
  text = re.sub('_\{(.*?)\}', r'<sub>\1</sub>', text)

  return mark_safe(text)


@register.filter
def is_admin(game, user):
  return game.is_admin(user)


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
  <img src='%(icon)s' alt='%(desc)s'>
  <span>%(name)s</span>
</div>
""" % {'icon': esc(realobj.icon),
       'desc': fancy(realobj.description, autoescape),
       'name': fancy(realobj.name, autoescape)})

icon.needs_autoescape = True
