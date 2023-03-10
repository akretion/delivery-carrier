# Copyright 2021 Akretion - Florian Mounier

{
    "name": "Delivery Carrier Mondial Relay",
    "version": "14.0.1.0.1",
    "summary": "Generate Label for Mondial Relay",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "category": "Warehouse",
    "depends": [
        "delivery_roulier_option",
        "document_url",  # url as attachments
        "intrastat_base",  # for customs declaration
    ],
    "data": [
        "data/delivery.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
