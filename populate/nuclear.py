

game = Game(name='Nuclear!', owner=user, key_name='nuclear')
game.put()


# Elementry category contains the base elements of the game.
cat_elementry = Category(game=game, name='Elementry', key_name='nuclear-elementry')

Element(game=game,
        name='Proton',
        category=cat_elementry,
        key_name='nuclear-proton').put()

Element(game=game,
        name='Electron',
        category=cat_elementry,
        key_name='nuclear-electron').put()

Element(game=game,
        name='Neutron',
        category=cat_elementry,
        key_name='nuclear-neutron').put()

###############################################################################

Element(game=game,
        name='Hydrogen',
        category=cat_elementry,
        key_name='nuclear-hydrogen').put()

Combination(game=game,
            key_name="nuclear-hydrogen",
            inputkeys=['nuclear-proton', 'nuclear-electron'],
            outputkeys=['nuclear-hydrogen']).put()

###############################################################################

Element(game=game,
        name='Positron',
        category=cat_elementry,
        key_name='nuclear-positron').put()

Element(game=game,
        name='Neutrino',
        category=cat_elementry,
        key_name='nuclear-neutrino').put()

Element(game=game,
        name='Deuterium',
        desc='Deuterium is an isotype for hydrogen with an extra neutron.',
        category=cat_elementry,
        key_name='nuclear-deuterium'
        ).put()

Combination(game=game,
            key_name="nuclear-deuterium",
            desc="""
The most basic nuclear fission reaction. Found in most stars.""",
            inputkeys=['nuclear-proton', 'nuclear-proton'],
            outputkeys=['nuclear-deuterium', 'nuclear-positron',
                        'nuclear-nuetrino']).put()

###############################################################################

Element(game=game,
        name='Photon',
        category=cat_elementry,
        key_name='nuclear-photon').put()

Combination(game=game,
            key_name="nuclear-photon",
            desc="""
Electron and positron annihilation, produces highly dangerous gama rays (high
energy photons).""",
            inputkeys=['nuclear-electron', 'nuclear-positron'],
            outputkeys=['nuclear-photon', 'nuclear-photon']).put()

###############################################################################

Element(game=game,
        name='Helium-3',
        desc='Helium 3 is an isotype of helium which is missing a neutron.',
        category=cat_elementry,
        key_name='nuclear-helium-3'
        ).put()

Combination(game=game,
            key_name="nuclear-annihilation",
            desc="""
Electron and positron annihilation, produces highly dangerous gama rays (high
energy photons).""",
            inputkeys=['nuclear-electron', 'nuclear-positron'],
            outputkeys=['nuclear-photon', 'nuclear-photon']).put()

###############################################################################
