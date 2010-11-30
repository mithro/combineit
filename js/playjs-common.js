/**
 * Copyright (c) 2010 Google Inc. All rights reserved.
 * Use of this source code is governed by a BSD-style license that can be
 * found in the LICENSE file.
 */

/* Code to setup the global cache of object information */
var atoms_by_userkey = {};
var atoms_by_globalkey = {};
var categories_by_userkey = {};
var categories_by_globalkey = {};
var combos_by_userkey = {};

function registerCategory(category) {
  category.atoms = [];

  categories_by_userkey[category.key] = category;
  categories_by_globalkey[category.reference.key] = category;
}

function registerAtom(atom) {
  atoms_by_userkey[atom.key] = atom;
  atoms_by_globalkey[atom.reference.key] = atom;

  categories_by_globalkey[
      atom.reference.category.key].atoms.push(atom);
}

function registerCombo(combo) {
  combos_by_userkey[combo.key] = combo;
}


function registerResults(callback, json) {
  for (i in json['results']) {
    callback(json['results'][i]);
  }
}

function registerCategories(json) {
  registerResults(registerCategory, json);
  $('body').append(
      $('<script></script>', {'src': "elements/my?output=json&callback=registerAtoms"}));
}

function registerAtoms(json) {
  registerResults(registerAtom, json);
  $('body').append(
      $('<script></script>', {'src': "combos/my?output=json&callback=registerCombos"}));
}

function registerCombos(json) {
  registerResults(registerCombo, json);
}

function getData() {
  $('body').append(
      $('<script></script>', {'src': "categories/my?output=json&callback=registerCategories"}));
}
