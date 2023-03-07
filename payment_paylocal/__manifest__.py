{
    'name': "PayLocal Payment Acquirer",
    'version': "15.0.1.0",
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Payment Acquirer: PayLocal Implementation',
    'description': """Integration with PayLocal Payment API""",
    'application': True,
    'uninstall_hook': 'uninstall_hook',
    'depends': ['payment'],
    'data': [
        'views/payment_acquirer.xml',
        'views/payment_paylocal_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_frontend': [
            'payment_paylocal/static/src/scss/payment_paylocal.scss',
            'payment_paylocal/static/src/js/payment_form_paylocal.js',
            'payment_paylocal/static/src/js/paylocal_client.js',
        ],
    },
    'license': "Other proprietary",
}
