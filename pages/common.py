#!/usr/bin/python2.5
#

import json
import logging
import pprint
import re
import urlparse

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from models import base
from models import stats


class BasePage(webapp.RequestHandler):
  """Base page which all others inherit from."""
  title = ''

  def setup(self, gameurl):
    """Setup some common information to all pages."""
    self.game = None

    # User needs to be logged in
    self.user = users.get_current_user()

    # Find the game object associated with this page..
    # FIXME: This seems like it should be somewhere else...
    self.game = base.Game.all().filter('url =', gameurl).get()
    if not self.game:
      return False

    return True

  def render(self, tmpl, result):
    """Render a template with some extra arguments to make it look nice."""
    output = self.request.get('output')

    if output == 'json':
      callback = re.sub('[^A-Za-z]', '', self.request.get('callback')).strip()

      if not callback:
        self.response.headers['Content-Type'] = 'application/json'
      else:
        self.response.headers['Content-Type'] = 'application/x-javascript'
        self.response.out.write('%s(' % callback)

      self.response.out.write(json.JSONEncoder().encode(result))

      if callback:
        self.response.out.write(');')

    elif output == 'text':
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write(pprint.pformat(result))

    else:
      logging.info('url %s', urlparse.urlparse(self.request.uri).path)


      result.update({
          'title': self.title,
          'path': urlparse.urlparse(self.request.uri).path,
          'login_url': users.create_login_url(self.request.uri),
          'logout_url': users.create_logout_url(self.request.uri),
          'game': self.game,
          'user': self.user,
          'is_current_user_admin': users.is_current_user_admin(),
          'featured_games': stats.FeaturedGame.all().fetch(10),
          'top_games': [],
          })

      self.response.headers['Content-Type'] = 'text/html; charset=utf-8'
      self.response.out.write(template.render(tmpl, result))

  def RenderBenchKeys(self, prefix, default=None):
    keys = self.request.get_all('%s_scratch' % prefix)
    if not keys and default:
      keys = default[:]

    keys = [x for x in keys if x]

    logging.info('key starting %r', keys)
    try:
      toremove = int(self.request.get('%s_remove' % prefix))
      logging.info('key toremove %r', toremove)
      del keys[toremove]
    except ValueError:
      pass

    toadd = self.request.get('%s_add' % prefix)
    if toadd:
      logging.info('key toadd %r', toadd)
      keys.append(toadd)

    logging.info('keys final %r', keys)
    return keys

    
class LoginPage(BasePage):
  """This page requires the user to be logged in to access."""

  def setup(self, gameurl):
    result = BasePage.setup(self, gameurl)

    if self.user is None:
      self.redirect(users.create_login_url(self.request.uri))
      return False

    return result


class GameAdminPage(LoginPage):
  """This page requires the person to be the admin of the game to access."""
  pass


class EditListPage(GameAdminPage):
  """List all entities of a given type that can be edited."""
  title = 'Edit List'

  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    logging.debug('EditListPage for %s', self.klass)

    query = self.klass.all()
    query.filter('game =', self.game)

    objects = [i for i in query.fetch(1000)]

    logging.warn(objects)

    self.render('templates/edit-list.html',
                {'objects': objects, 'url': self.url})


class EditPage(GameAdminPage):
  """Edit an entity."""

  title = 'Edit'
  fields = ("name", "description", "icon")

  def common(self, gameurl):
    if not self.setup(gameurl):
      return

    key = self.request.get('key')
    if key:
      object = self.klass.get(key)
    else:
      object = self.klass(game=self.game)

    for attr in self.fields:
      attr_value = self.request.get(attr).strip()
      if attr_value:
        setattr(object, attr, attr_value)

    return object

  def get(self, gameurl):
    obj = self.common(gameurl)
    if not obj:
      return

    self.render(obj)


class DeletePage(GameAdminPage):
  """Delete an entity."""

  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    key = self.request.get('key')
    object = self.klass.get(key)
    object.delete()
    self.redirect('/%s/%s/list' % (self.game.url, self.url))
