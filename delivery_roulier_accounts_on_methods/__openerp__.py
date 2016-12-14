# coding: utf-8
# @author Raphael Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Accounts on delivery methods',
    'version': '9.0.0.0.0',
    'author': 'Akretion',
    'summary': 'Set an account on delivery methods',
    'maintainer': 'Akretion, Odoo Community Association (OCA)',
    'category': 'Warehouse',
    'depends': [
        'keychain',
        'delivery_roulier',
    ],
    'website': 'http://www.akretion.com/',
    'data': [
        'views/delivery.xml',
    ],
    'demo': [
    ],
    'external_dependencies': {
    },
    'tests': [],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
