# coding: utf-8
# © 2017 Raphael REVERDY <raphael.reverdy@akretion.com>
#        David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Delivery Carrier La Poste (fr)',
    'version': '10.0.1.0.1',
    'author': 'Akretion',
    'summary': 'Generate Label for La Poste/Colissimo',
    'maintainer': 'Akretion,Odoo Community Association (OCA)',
    'category': 'Warehouse',
    'depends': [
        'delivery_roulier',
        'delivery_roulier_option',
        'intrastat_base',  # for customs declaration
    ],
    'website': 'http://www.akretion.com/',
    'data': [
        'data/delivery.xml',
        'data/keychain.xml',
        'views/stock_picking.xml',
        'views/keychain_backend.xml',
    ],
    'external_dependencies': {
        'python': [
            'roulier',
        ]
    },
    'installable': True,
    'license': 'AGPL-3',
}
