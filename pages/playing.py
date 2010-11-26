"""Module which contains pages for actually playing the game."""

import logging

from google.appengine.ext import db
from google.appengine.ext.webapp import template

from django.utils.safestring import mark_safe

import common
from models import base
from models import peruser


class IndexPage(common.BasePage):
  """The front page of the system."""

  def get(self):
    self.setup('')

    query = base.Game.all()
    games = [i for i in query.fetch(1000)]

    self.render(
        'templates/index.html', {'games': games})


class StartPage(common.LoginPage):
  """Page which populates the user with all the starting game information."""
  pass


class AbandonPage(common.LoginPage):
  """Page which deletes all the game information for the given user."""

  # FIXME: This page needs XSRF protection!

  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    categories_query = peruser.UsersCategory.all(keys_only=True)
    categories_query.filter('game =', self.game)
    categories_query.filter('user =', self.user)
    db.delete(categories_query.fetch(1000))

    elements_query = peruser.UsersElement.all(keys_only=True)
    elements_query.filter('game =', self.game)
    elements_query.filter('user =', self.user)
    db.delete(elements_query.fetch(1000))

    combos_query = peruser.UsersCombination.all(keys_only=True)
    combos_query.filter('game =', self.game)
    combos_query.filter('user =', self.user)
    db.delete(combos_query.fetch(1000))

    self.redirect('/')


class PlayJSPage(common.LoginPage):
  """A Page which is javascript based."""

  def post(self, gameurl):
    if not self.setup(gameurl):
      return

    if self.request.get('mobile'):
      return self.render('templates/playjs-mobile.html', {})
    else:
      return self.render('templates/playjs.html', {})

  get = post


class PlayPage(common.LoginPage):
  """Page which actually lets you play the game."""

  def RenderUserBench(self, prefix, thisform, submitform=None):
    # FIXME: This doesn't belong on this class

    # Get all the elements in the current "scratch area"
    keys = self.RenderBenchKeys(prefix, [])
    if keys:
      scratch = peruser.UsersElement.get(keys)
    else:
      scratch = []

    # Work out which category is currently display on the bench.
    query = peruser.UsersCategory.all()
    query.filter('game =', self.game)
    query.filter('user =', self.user)
    categories = query.fetch(1000)

    # Populate the database
    if not categories:
      for category_key in self.game.starting_categories:
        category = base.Category.get(category_key)

        categories.append(
            peruser.UsersCategory.Create(self.user, self.game, category))

      for element_key in self.game.starting_elements:
        element = base.Element.get(element_key)
        peruser.UsersElement.Create(self.user, self.game, element)

    selected_category_key = self.request.get(prefix+'_category')
    try:
      selected_category = peruser.UsersCategory.get(selected_category_key)
    except db.BadKeyError, e:
      selected_category = categories[0]

    query = peruser.UsersElement.all()
    query.filter('game =', self.game)
    query.filter('user =', self.user)
    query.filter('category =', selected_category.reference)
    elements = query.fetch(1000)

    if not submitform:
      submitform = thisform

    # Render out the bench
    html = template.render(
        'templates/bench.html',
        {'submitform': submitform,
         'thisform': thisform,
         'scratch': scratch,
         'categories': categories,
         'elements': elements,
         'selected_category': selected_category,
         'prefix': prefix})

    return mark_safe(html), scratch

  def post(self, gameurl):
    if not self.setup(gameurl):
      return

    scratch_html, elements = self.RenderUserBench('scratch', thisform='scratch', submitform='bench')
    return self.render('templates/play.html', {
        'scratch': elements,
        'scratch_bench': scratch_html,
        })

  get = post


class CombinePage(common.LoginPage):
  """This page actually does all the work, it takes a list of elements to
  combind and returns if the combination is successful.

  It also returns if any of the elements or categories are new.
  """
  def post(self, gameurl):
    if not self.setup(gameurl):
      return

    userselementids = self.request.get_all('tocombined[]')
    userselementids = list(sorted(userselementids))
    logging.info('userselementids %s', userselementids)
    if not userselementids:
      self.render('templates/nocombine.html', {
          'code': 404, 'error': 'No input!'})
      return

    userselements = peruser.UsersElement.get(userselementids)
    logging.info(userselements)
    logging.info([x for x in userselements if x])
    if len([x for x in userselements if x]) != len(userselements):
      self.render('templates/nocombine.html', {
          'code': 404, 'error': 'Unknown element!'})
      return

    elements = [str(x.reference.key()) for x in userselements]

    query = base.Combination.all()
    for element in elements:
      query.filter('inputkeys =', element)

    results = query.fetch(1000)
    logging.debug('results %s', results)

    if not results:
      self.render('templates/nocombine.html', {
          'code': 404, 'error': 'No dice!'})
      return

    for combination in results:
      # Check the match is exact
      tomatch = []
      for elementid in combination.inputkeys:
        tomatch.append(elementid)
      tomatch = list(sorted(tomatch))

      if elements == tomatch:
        break
    else:
      self.render('templates/nocombine.html', {
          'code': 302, 'error': 'Almost!'})
      return

    new_usercombination = peruser.UsersCombination.Create(
        self.user, self.game, combination)
    if not new_usercombination:
      query = peruser.UsersCombination.all()
      query.filter('game =', self.game)
      query.filter('user =', self.user)
      query.filter('reference =', combination)
      usercombination = query.get()
    else:
      usercombination = new_usercombination
      new_usercombination = True

    categories = set()
    new_userelements = set()
    for element in combination.output():
      categories.add(element.category)

      userelement = peruser.UsersElement.Create(self.user, self.game, element)
      if userelement:
        new_userelements.add(userelement)

    new_usercategories = set()
    for category in categories:
      usercategory = peruser.UsersCategory.Create(self.user, self.game, category)
      if usercategory:
        new_usercategories.add(usercategory)

    return self.render(
        'templates/combine.html',
        {'code': 200,
         'new_usercombination': new_usercombination,
         'usercombination': usercombination,
         'new_userelements': new_userelements,
         'new_usercategories': new_usercategories})
