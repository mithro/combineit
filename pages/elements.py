# Copyright (c) 2010 Google Inc. All rights reserved.
# Use of this source code is governed by a Apache-style license that can be
# found in the LICENSE file.

"""Module for all things dealing with Elements."""

import common
from models import base
from models import peruser


class ElementListPage(common.EditListPage):
  url = "elements"
  klass = base.Element


class ElementEditPage(common.EditPage):
  url = "elements"
  klass = base.Element

  def post(self, gameurl):
    element = self.common(gameurl)
    element.category = base.Category.get(self.request.get('category'))
    element.put()

    self.render(element)

  def render(self, element):
    query = base.Category.all()
    query.filter('game =', self.game)
    categories = query.fetch(1000)

    common.EditPage.render(
        self, 'templates/edit-element.html',
        {'object': element,
         'categories': categories})


class ElementDeletePage(common.DeletePage):
  url = "elements"
  klass = base.Element


class ElementPage(common.LoginPage):
  """Get a list of elements for a user."""
  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    query = peruser.UsersElement.all()
    query.filter('user =', self.user)
    query.filter('game =', self.game)
    results = query.fetch(1000)

    return self.render('templates/list.html', {'results': results})
