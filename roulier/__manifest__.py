# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Roulier",
    "version": "18.0.1.0.0",
    "author": "Akretion, Odoo Community Association (OCA)",
    "summary": "Integration of Roulier carriers",
    "category": "Delivery",
    "depends": [
        "delivery_carrier_account",
        "delivery_carrier_info",
        "delivery_carrier_shipping_label",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "views/delivery_carrier_views.xml",
        "views/carrier_account_views.xml",
    ],
    "maintainers": ["paradoxxxzero"],
    "demo": [],
    "installable": True,
    "license": "AGPL-3",
    "assets": {
        "web.assets_backend": [
            "roulier/static/src/scss/properties.scss",
        ]
    },
}
