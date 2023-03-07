# -*- coding: utf-8 -*-
{
    'name': "navigo_menucusts",
    'summary': """User menu customizations""",
    'description': """Core menu customizacions""",
    'author': "Navigo-inc",
    'website': "https://www.navigo-inc.com",
    'category': 'Extra',
    'version': '0.1',
    'depends': ['base','web'],
    'assets': {
        'web._assets_primary_variables': [
            ('replace', 'web/static/src/legacy/scss/primary_variables.scss', '/navigo_menucusts/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_backend': [
            ('replace', 'web/static/src/webclient/user_menu/user_menu_items.js', '/navigo_menucusts/static/src/user_menu/user_menu_items.js'),
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
