# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    directional_code_id = fields.Many2one(
        comodel_name="kuehne.directional.code",
        string="Directional code",
        compute="_compute_directional_code_id",
        store=True,
        readonly=False,
    )

    def action_confirm(self):
        """
        Set the route montage in case of assembled products
        Send mail to the customer when confirm
        """
        self.ensure_one()
        res = super().action_confirm()
        if res is True:
            for sale in self:
                if (
                    not sale.directional_code_id
                    and sale.carrier_id.delivery_type == "kuehne_nagel_fr"
                ):
                    sale.send_missing_directional_code_email()
        return res

    def send_missing_directional_code_email(self):
        self.ensure_one()
        tmp = "delivery_roulier_kuehne_nagel_fr.missing_directional_code_template"
        email_template = self.env.ref(tmp)
        email_template.send_mail(self.id)

    def write(self, vals):
        # send mail for all sale orders if new carrier is kuehne and old one was not
        # if the directional_code_id is not set.
        orders_to_notify = self.env["sale.order"]
        if vals.get("carrier_id"):
            new_carrier = self.env["delivery.carrier"].browse(vals["carrier_id"])
            if new_carrier.delivery_type == "kuehne_nagel_fr":
                orders_to_notify = self.filtered(
                    lambda so: so.carrier_id.delivery_type != "kuehne_nagel_fr"
                    and not so.directional_code_id
                    and so.state in ("sale", "done")
                )
        res = super().write(vals)
        for order_to_notify in orders_to_notify:
            order_to_notify.send_missing_directional_code_email()
        return res

    @api.depends("partner_shipping_id")
    def _compute_directional_code_id(self):
        directional_code_obj = self.env["kuehne.directional.code"]
        for sale in self:
            partner = sale.partner_shipping_id
            if partner.zip:
                code = directional_code_obj._search_directional_code(
                    sale.company_id.country_id.id,
                    partner.country_id.id,
                    partner.zip,
                    partner.city,
                )
                if code and len(code) == 1:
                    sale.directional_code_id = code.id
