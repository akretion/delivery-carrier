# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    #    kuehne_meta = fields.Text(
    #        "meta",
    #        help="Needed for deposit slip",
    #    )
    #    kuehne_meta_footer = fields.Text(
    #        "meta footer",
    #        help="Needed for deposit slip",
    #    )
    #
    #    def kuehne_get_meta(self):
    #        self.ensure_one()
    #        parcels = self._get_packages_from_picking().kuehne_get_meta()
    #        meta = "%s\n%s\n%s" % (self.kuehne_meta, parcels, self.kuehne_meta_footer)
    #        return meta

    def _kuehne_nagel_fr_get_from_address(self, package=None):
        vals = self._roulier_get_from_address(package=package)
        sender_name = "%s/%s/%s/%s" % (
            self.company_id.name,
            self.company_id.country_id.code.upper(),
            self.company_id.zip,
            self.company_id.city,
        )
        vals["company"] = sender_name
        return vals

    def _kuehne_nagel_fr_get_service(self, account, package=False):
        directional_code = self._kuehne_get_directional_code()
        service = self._roulier_get_service(account, package=package)
        contract = account.kuehne_delivery_contract
        map_delivery_contract = {
            "GSP": "F",
            "GFX": "D",
        }
        label_delivery_contract = map_delivery_contract.get(contract, "C")
        office_name = "KUEHNE NAGEL ROAD / AG : %s %s %s" % (
            account.kuehne_office_country_id.code.upper(),
            account.kuehne_office_code,
            account.kuehne_office_name,
        )
        service.update(
            {
                "customerId": account.kuehne_sender_id,
                "goodsName": account.kuehne_goods_name,
                "shippingOffice": directional_code["office"],
                "shippingRound": directional_code["round"],
                "exportHub": directional_code["export_hub"],
                "shippingName": self.name.replace("/", ""),
                "deliveryContract": contract or "",
                "labelDeliveryContract": label_delivery_contract,
                "orderName": self.sale_id.name or self.origin,
                "shippingConfig": account.kuehne_shipping_config,
                "vatConfig": account.kuehne_vat_config,
                "deliveryType": self.carrier_id.kuehne_delivery_mode,
                "note": self.note and self.note or "",
                "labelLogo": account.kuehne_label_logo,
                "kuehneOfficeName": office_name,
            }
        )
        return service

    def _kuehne_nagel_fr_get_shipping_date(self, package=None):
        return self.date_done or fields.Date.today()

    def _kuehne_get_directional_code(self):
        self.ensure_one()
        directional_code = False
        directional_code_obj = self.env["kuehne.directional.code"]
        if self.sale_id and self.sale_id.directional_code_id:
            directional_code = self.sale_id.directional_code_id
        else:
            directional_code = directional_code_obj._search_directional_code(
                self.company_id.country_id.id,
                self.partner_id.country_id.id,
                self.partner_id.zip,
                self.partner_id.city,
            )
        if not directional_code:
            raise UserError(
                _("No directional code found for the picking %s !") % self.id
            )
        return {
            "office": directional_code.office_code,
            "round": directional_code.office_round,
            "export_hub": directional_code.export_hub,
        }

    def _kuehne_nagel_fr_support_multi_tracking(self):
        return False
