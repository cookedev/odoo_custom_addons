# -*- coding: utf-8 -*-
{
    'name': "Navigo's Website Snippets",

    'summary': """
        Navigo's custom snippets collection
        """,

    'description': """
        No further commets here yet
    """,

    'author': "Navigo Inc.",
    'website': "https://www.navigo-inc.com",

    'category': 'Extra',
    'version': '0.1',

    'depends': ['base','web','website_profile'],

    'data': [
        'views/snippets.xml',
    ],

    'assets': {
            'web.assets_frontend': [
                'navigo_snippets/static/src/scss/main.scss',
            ],
        },

}
