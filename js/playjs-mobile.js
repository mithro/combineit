/**
 * Copyright (c) 2010 Google Inc. All rights reserved.
 * Use of this source code is governed by a BSD-style license that can be
 * found in the LICENSE file.
 */

function listIcon(obj, href, count) {
  var li = $('<li></li>');

  $('<img />', {src: obj.reference.icon,
                alt: obj.reference.description}).appendTo(li);

  $('<h3></h3>').append(
      $('<a/>',
        {href: href,
         text: obj.reference.name,
         key: obj.key})).appendTo(li);

  $('<p></p>', {text: obj.reference.description}).appendTo(li);
  if (count) {
    $('<span></span>', {text:""+count, "class": "ui-li-count"}).appendTo(li);
  }
  return li;
}

function objectIcon(obj) {
  return $('<div></div>').append(
      $('<a />', {href: '#', 'data-role': 'button', key: obj.key})
      .append(
        $('<img />', {src: obj.reference.icon, 'class': 'icon'}))
      .append(
        $('<span />', {'class': 'icon-text', 'text': obj.reference.name})
      ));
}

function buildBenchTop() {
  // Clear out any selected icons
  $('#bench-top').empty();
}

function buildCategories() {
  var categorieslist = $('#categories');

  // Clear out the old list
  categorieslist.empty();

  for (categorykey in categories_by_userkey) {
    var category = categories_by_userkey[categorykey];

    categorieslist.append(
        listIcon(category, '#'+categorykey, category.atoms.length));

    // Update/create the category pages
    var categorypage = $('#'+categorykey);
    if (categorypage.length == 0) {
      // Category page doesn't exist, so lets create it
      var categorypage = $('<div />', {'data-role': 'page', id: categorykey});

      // Add the header
      categorypage.append(
          $('<div />', {'data-role': 'header', 'data-theme': 'b'}).append(
              $('<h1>', {'text': category.reference.name})));

      // Add the body
      categorypage.append(
          $('<div />', {'data-role': 'content'}).append(
              $('<ul />', {'data-role': 'listview'})));

      $('body').append(categorypage);
      categorypage.page();
    }

    // Create the element list for the category.
    var list = categorypage.find('ul');
    list.empty();

    for (i in category.atoms) {
      var atom = category.atoms[i];

      list.append(
          listIcon(atom, 'javascript: addAtom("'+atom.key+'");'));
    }
    list.listview('refresh');
  }

  categorieslist.listview('refresh');
}

function build() {
  buildBenchTop();
  buildCategories();
}

/* Functions which actually play the game. */

function updateGrid(divs, callback) {

  divs.each(function(x, div) {
    div = $(div);
    div.click(function() {
      callback(x);
    });
    div.removeClass('ui-block-a');
    div.removeClass('ui-block-b');
    div.removeClass('ui-block-c');

    div.addClass(['ui-block-a', 'ui-block-b', 'ui-block-c'][x % 3]);
    // FIXME: This is kinda nasty...
    div.page();
  });
}

function updateBenchTop() {
  var divs = $('#bench-top div');
  updateGrid(divs, removeAtom);

  if (divs.length == 0) {
    // FIXME: Disable the blend button here.
  } else {
  }
}

function addAtom(atomkey) {
  var atom = atoms_by_userkey[atomkey];

  var benchtop = $('#bench-top');

  objectIcon(atom).appendTo(benchtop);

  updateBenchTop();
  window.location.hash = '';
}

function removeAtom(index) {
  var divs = $('#bench-top div');

  var item = $(divs[index]);
  item.detach();

  updateBenchTop();
}

function blendItBaby() {
  if ($.mobile.pageLoading())
    return;

  var atom_keys = [];

  $('#bench-top a').each(function(i, atomui) {
    atom_keys.push($(atomui).attr('key'));
  });

  // FIXME: Handle ajax call failure...
  ajaxCall = $.ajax({
    url: 'combine',
    dataType: 'json',
    type: 'POST',
    data: {'output':'json',
           'tocombined': atom_keys},
    success: blendedCallback,
  });
}

function blendedCallback(json) {
  $('#result').detach();

  var resultpage = $(
      '<div></div>', {id: 'result', 'data-role': 'dialog'});
  var resultcontent = $(
      '<div></div>', {id: 'result-content', 'data-role': 'content', 'data-theme': 'a'}).appendTo(resultpage);

  if (json.code == 200) {
    $.each(json.new_usercategories, function(i, category) {
      registerCategory(category);
    });

    $.each(json.new_userelements, function(i, atom) {
      registerAtom(atom);
    });

    var input = $('<div></div>', {'class': 'ui-grid-a'}).appendTo(resultcontent);
    $.each(json.usercombination.reference.inputkeys, function(i, atomkey) {
      input.append(objectIcon(atoms_by_globalkey[atomkey]));
    });

    updateGrid(input.find('div'), function() {});

    $('<p>to</p>').appendTo(resultcontent);

    var output = $('<div></div>', {'class': 'ui-grid-b'}).appendTo(resultcontent);
    $.each(json.usercombination.reference.outputkeys, function(i, atomkey) {
      output.append(objectIcon(atoms_by_globalkey[atomkey]));
    });

    updateGrid(output.find('div'), function() {});
  }

  resultcontent.append(
      $('<a data-role="button" data-theme="a">Cool!</a>').click(
          function() {
            $('#result').dialog('close');
          }));

  buildBenchTop();
  buildCategories();

  $('body').append(resultpage);
  resultpage.page();
  $.mobile.pageLoading(true);

  $.mobile.changePage(resultpage, "slidedown");
}



$(document).ready(build);
