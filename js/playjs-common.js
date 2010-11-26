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
}

function registerAtoms(json) {
  registerResults(registerAtom, json);
}

function registerCombos(json) {
  registerResults(registerCombo, json);
}
