/**
 * Copyright (c) 2010 Google Inc. All rights reserved.
 * Use of this source code is governed by a BSD-style license that can be
 * found in the LICENSE file.
 */

function objectIcon(obj, callback, nodiv) {

  var link = $("<a/>", {href: "#", key: obj.key, click: function() {
    callback(obj, link);
  }});

  var appendto = null;
  if (nodiv) {
    var appendto = link;
  } else {
    var appendto = $("<div/>", {"class": "icon"}).appendTo(link);
  }
  var span = $("<span/>", {text: obj.reference.name}).appendTo(appendto);
  var img  = $("<img />", {src: obj.reference.icon,
                           alt: obj.reference.description}).appendTo(appendto);
  return link;
}

function buildBenchTop() {
  var benchtop = $('#bench-top');

  benchtop.empty();

  benchtop.droppable({
     accept: ".atom",
     activeClass: "ui-state-highlight",
     drop: addDroppedAtom
  });

  $('#blend').button().click(blendItBaby);
}

var ajaxCall = null;

function blendItBaby() {
  if (ajaxCall)
    return;

  var atom_keys = [];

  $('#bench-top a.atom').each(function(i, atomui) {
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
  var dialog = $('#dialog');
  
  var title = '';

  if (json.code == 200) {
    $.each(json.new_usercategories, function(i, category) {
      registerCategory(category);
    });

    $.each(json.new_userelements, function(i, atom) {
      registerAtom(atom);
    });


    var title = '';
    if (json.new_usercombination) {
      title = 'New combination discovered!';
    } else {
      title = 'Combination already discovered';
    }

    var table = $('<table/>', {'class': 'dialog'});
    dialog.append(table);

    var inputtr = $('<tr/>');
    table.append(inputtr);

    var input = $('<tr>').appendTo(
      $('<table>').appendTo(
        $('<td>', {'class': 'input'}).appendTo(
          inputtr)));
    $.each(json.usercombination.reference.inputkeys, function(i, atomkey) {
      input.append($('<td>').append(
        objectIcon(atoms_by_globalkey[atomkey], function() {})
        ));
    });

    table.append($('<tr/>').append(
      $('<td>', {'class': 'arrow'}).append(
        $('<img />', {src: '/images/down.png'}))));

    var output = $('<tr>').appendTo(
      $('<table>').appendTo(
        $('<td>', {'class': 'output'}).appendTo(
          $('<tr>').appendTo(
            table))));
    $.each(json.usercombination.reference.outputkeys, function(i, atomkey) {
      output.append($('<td>').append(
        objectIcon(atoms_by_globalkey[atomkey], function() {})
        ));
    });

    inputtr.append($('<td/>', {rowspan: 3, 'class': 'desc'}).append(
      $('<h1>' + json.usercombination.reference.name + '</h1>')).append(
      $('<span>' + json.usercombination.reference.description + '</span>')));

  } else {
    title = json.error;
  }

  function onClose() {
    $( this ).empty();
    build();

    ajaxCall = null;
  }

  function onOkay() {
    $( this ).dialog( "close" );
    onClose();
  }

  dialog.dialog({
      autoOpen: false,
      draggable: false,
      resizable: false,
      modal: true,
      show: "blind",
      hide: "blind",
      width: "90%",
      title: title,
      close: onClose,
      buttons: { Ok: onOkay }
      });

  dialog.dialog( "open" );
}

function buildCategories() {
  var bench = $('#bench-categories');
  var f = bench.children('.container');

  f.empty();

  for (categorykey in categories_by_userkey) {
    var category = categories_by_userkey[categorykey];

    var link = objectIcon(category, showAtoms, true);
    link.addClass('fisheye-item');
    f.append(link);
  }

  bench.Fisheye({
    maxWidth: 128,
    items: 'a',
    itemsText: 'span',
    container: '.fisheye-container',
    itemWidth: 40,
    proximity: 80,
    alignment: 'left',
    valign: 'bottom',
    halign : 'center'});
}

function buildAtoms() {
  var bench = $('#bench-atoms');

  bench.empty();

  for (categorykey in categories_by_userkey) {
    var category = categories_by_userkey[categorykey];

    var div = $('<div/>', {id: categorykey, "class": "atoms"});
    for (i in category.atoms) {
      var atom = category.atoms[i];

      var link = objectIcon(atom, addAtom);
      link.addClass('atom');

      link.draggable({
          revert: 'invalid',
          helper: 'clone'
      });

      div.append(link);
    }

    bench.append(div);

  }
  showAtoms(category);
}

function build() {
  buildBenchTop();
  buildCategories();
  buildAtoms();
}

/* Functions which actually play the game. */

function showAtoms(category, ui) {
  $('#bench-atoms div.atoms').hide();
  $('#'+category.key).show();
}

function addDroppedAtom(element, ui) {
  addAtom(null, ui.draggable);
}

function addAtom(obj, ui) {
  var newelement = ui.clone();

  newelement.click(function() {
    $(this).remove();
  });

  $('#bench-top').append(newelement);
}

$(document).ready(build);
