# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    kuehne_shipping_config = fields.Selection(
        [("P", "Paid shipping cost"), ("C", "Due shipping cost"), ("F", "Service")],
        string="Shipping",
        default="P",
    )
    kuehne_vat_config = fields.Selection(
        [("V", "VAT payable"), ("E", "VAT exempt")],
        string="VAT",
        default="V",
    )
    kuehne_delivery_contract = fields.Selection(
        [("GSP", "KN EuroLink First"), ("GFX", "KN EuroLink Fix")],
        string="Delivery contract",
    )
    kuehne_sender_id = fields.Char(help="Used to build the tracking url")
    kuehne_goods_name = fields.Char("Kuehne Nagel Goods Name")
    kuehne_label_logo = fields.Text(string="Logo for Kuehne Shipping Label")

    # It seems kuhene needs a different account (invoice contract) per agency.
    # so, to ease the configuration and have everything at the same place, we put
    # the agency information here. If it becomes an issue for some usecase
    # we could depend on module delivery_carrier_agency and put this information
    # there.
    kuehne_siret = fields.Char()
    kuehne_office_name = fields.Char("Kuehne Nagel Office Name")
    kuehne_office_country_id = fields.Many2one(
        comodel_name="res.country", string="Kuehne Nagel Office Country"
    )
    kuehne_office_code = fields.Char("Kuehne Nagel Office Code")
