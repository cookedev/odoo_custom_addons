{
    'name': "Assign User Groups",
    'summary': """Allows select users to create other users and assign them to certain security groups""",
    'description': """""",
    'author': "Christian McClanahan",
    'website': "https://github.com/PayLocalUs/munition-universe-odoo",
    'category': 'Uncategorized',
    'version': '15.0.0.1.2',
    # 'depends': ['base', 'web', 'base_setup'],
    'depends': ['base'],
    'data': [
        'views/res_users.xml',
    ],
    'license': 'Other proprietary',
}
