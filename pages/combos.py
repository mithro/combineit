"""Module for all things dealing with Combinations."""

import logging

from google.appengine.ext import db
from google.appengine.ext.webapp import template

from django.utils.safestring import mark_safe

import common
from models import base
from models import peruser


class ComboListPage(common.EditListPage):
  url = "combos"
  klass = base.Combination


class ComboEditPage(common.EditPage):
  url = "combo"
  klass = base.Combination
  fields = ("name", "description")

  def RenderAdminBench(self, prefix, thisform, defaultkeys=None):
    # Get all the elements in the current "scratch area"
    keys = self.RenderBenchKeys(prefix, defaultkeys)
    logging.info('keys final %r', keys)
    if keys:
      scratch = base.Element.get(keys)
    else:
      scratch = []

    # Work out which category is currently display on the bench.
    query = base.Category.all()
    query.filter('game =', self.game)
    categories = query.fetch(1000)

    selected_category_key = self.request.get(prefix+'_category')
    try:
      selected_category = base.Category.get(selected_category_key)
    except db.BadKeyError, e:
      selected_category = categories[0]

    query = base.Element.all()
    query.filter('game =', self.game)
    query.filter('category =', selected_category)
    elements = query.fetch(1000)

    # Render out the bench
    html = template.render(
        'templates/bench.html',
        {'submitform': thisform,
         'thisform': thisform,
         'scratch': scratch,
         'categories': categories,
         'elements': elements,
         'selected_category': selected_category,
         'prefix': prefix})

    return mark_safe(html), scratch

  def post(self, gameurl):
    combo = self.common(gameurl)
    if not combo:
      return

    self.render(combo)

    # Quick Create doesn't set this..
    if self.request.get('action') == 'Save':
      combo.put()

  def render(self, combo):
    input_html, input_elements = self.RenderAdminBench(
        'input', thisform='edit', defaultkeys=combo.inputkeys)
    if input_elements:
      combo.inputkeys = [str(x.key()) for x in input_elements]

    output_html, output_elements = self.RenderAdminBench(
        'output', thisform='edit', defaultkeys=combo.outputkeys)
    if output_elements:
      combo.outputkeys = [str(x.key()) for x in output_elements]

    common.EditPage.render(
        self, 'templates/edit-combo.html',
        {'object': combo,
         'input_bench': input_html,
         'output_bench': output_html})


class ComboDeletePage(common.DeletePage):
  url = "combos"
  klass = base.Combination


class ComboPage(common.LoginPage):
  """Get a list of elements for a user."""
  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    query = peruser.UsersCombination.all()
    query.filter('user =', self.user)
    query.filter('game =', self.game)
    results = query.fetch(1000)

    return self.render('templates/list.html', {'results': results})
