#!/usr/bin/python2.5
#

"""This module represents what people have voted for."""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.1')
import django_extra

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from pages import categories
from pages import combos
from pages import elements
from pages import games
from pages import playing


application = webapp.WSGIApplication(
  [('/',                       playing.IndexPage),
   ('/(.*)/start',             playing.StartPage),
   ('/(.*)/combine',           playing.CombinePage),
   ('/(.*)/play',              playing.PlayPage),
   ('/(.*)/abandon',           playing.AbandonPage),
   ('/(.*)/elements',          elements.ElementPage),
   ('/(.*)/elements/list',     elements.ElementListPage),
   ('/(.*)/elements/edit',     elements.ElementEditPage),
   ('/(.*)/elements/delete',   elements.ElementDeletePage),
   ('/(.*)/elements/my',       elements.ElementPage),
   ('/(.*)/categories',        categories.CategoryPage),
   ('/(.*)/categories/list',   categories.CategoryListPage),
   ('/(.*)/categories/edit',   categories.CategoryEditPage),
   ('/(.*)/categories/delete', categories.CategoryDeletePage),
   ('/(.*)/categories/my',     categories.CategoryPage),
   ('/(.*)/combos',            combos.ComboPage),
   ('/(.*)/combos/list',       combos.ComboListPage),
   ('/(.*)/combos/edit',       combos.ComboEditPage),
   ('/(.*)/combos/delete',     combos.ComboDeletePage),
   ('/(.*)/combos/my',         combos.ComboPage),
   ('/games/edit',             games.GameEditPage),
   ('/games/delete',           games.GameDeletePage),
   ('/(.*)/edit',              games.GameEditRedirect),
   ],
  debug=True)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
