# -*- coding: utf-8 -*-

{
    'name': 'Kuehne Nagel',
    'version': '0.3',
    'author': 'Akretion',
    'summary': 'Ship with Kuehne & Nagel carrier',
    'maintainer': 'Akretion',
    'category': 'Warehouse',
    'depends': [
        'delivery_carrier_b2c',
        'delivery_roulier',
        'delivery_carrier_deposit',
        'external_file_location',
    ],
    'description': """
Delivery Carrier Kuehne Nagel
=============================


Description
-----------


Technical references
--------------------

Contributors
------------

* Benoit GUILLOT <benoit.guillot@akretion.com>

----

    """,
    'website': 'http://www.akretion.com/',
    'data': [
        'data/external_file.xml',
        'data/email_template.xml',
        'views/config_view.xml',
        'views/stock_view.xml',
        'views/sale_view.xml',
        'views/directional_code_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'external_dependencies': {
        'python': [
            'roulier',
            'unicodecsv',
        ],
    },
    'tests': [],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
