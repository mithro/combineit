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
  var dialog = $('<div />');

  if (json.code == 200) {
    $.each(json.new_usercategories, function(i, category) {
      registerCategory(category);
    });

    $.each(json.new_userelements, function(i, atom) {
      registerAtom(atom);
    });

    var message = $("<div/>");
    if (json.new_usercombination) {
      message.append($("<h1>NEW!</h1>"));
    }
    message.append($("<h1>" + json.usercombination.reference.name + "</h1>"));

    var input = $('<div/>');
    $.each(json.usercombination.reference.inputkeys, function(i, atomkey) {
      input.append(
        objectIcon(atoms_by_globalkey[atomkey], function() {})
        );
    });

    var output = $('<div/>');
    $.each(json.usercombination.reference.outputkeys, function(i, atomkey) {
      output.append(
        objectIcon(atoms_by_globalkey[atomkey], function() {})
        );
    });

    dialog.append(message);
    dialog.append(input);
    dialog.append(output);

  } else {
    dialog.append($("<h1>" + json.error + "</h1>"));
  }

  function onClose() {
    $( this ).dialog( "close" );
    build();

    ajaxCall = null;
  }

  dialog.dialog({
    width: "90%",
    modal: true,
    buttons: { Ok: onClose }
    });
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
