"""Module for all things dealing with Categories."""

import common
from models import base
from models import peruser


class CategoryListPage(common.EditListPage):
  url = "categories"
  klass = base.Category


class CategoryEditPage(common.EditPage):
  url = "categories"
  klass = base.Category

  def post(self, gameurl):
    category = self.common(gameurl)
    category.put()

    self.render(category)

  def render(self, category):
    common.EditPage.render(
        self, 'templates/edit-category.html',
        {'object': category})


class CategoryDeletePage(common.DeletePage):
  url = "categories"
  klass = base.Category


class CategoryPage(common.LoginPage):
  """Get a list of categories for a user."""
  def get(self, gameurl):
    if not self.setup(gameurl):
      return

    query = peruser.UsersCategory.all()
    query.filter('user =', self.user)
    query.filter('game =', self.game)
    results = query.fetch(1000)

    return self.render('templates/list.html', {'results': results})
