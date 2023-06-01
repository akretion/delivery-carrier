# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from base64 import b64encode
from datetime import datetime

from roulier import roulier

from odoo import models


class DepositSlip(models.Model):
    _inherit = "deposit.slip"

    def _kuehne_prepare_edi_payload(self):
        first_picking = self.picking_ids[0]
        # we consider picking from deposit slip are consistent, not our rôle to make
        # sure of it ?
        account = first_picking._get_account(self)

        payload = {
            "sender_info": {
                "number": self.company_id.siren,
                "siret": self.company_id.siret,
                "name": self.company_id.name,
            },
            "recipient_info": {
                "number": account.kuehne_siret[:9],
                "siret": account.kuehne_siret,
                "name": account.kuehne_office_name,
            },
        }
        payload["auth"] = first_picking._get_auth(account)
        payload["shipments"] = []
        for picking in self.picking_ids:
            packages = picking.package_ids
            picking_payload = {}
            picking_payload["to_address"] = picking._get_to_address(package=packages)
            picking_payload["service"] = picking._get_service(account, package=packages)
            picking_payload["parcels"] = packages._get_parcels(picking)
            payload["shipments"].append(picking_payload)

        now = datetime.now()
        date = now.date().strftime("%y%m%d")
        hour = now.time().strftime("%H%M")
        contract = account.kuehne_delivery_contract

        payload["service"] = {
            "date": date,
            "hour": hour,
            "depositNumber": self.name,
            "deliveryContract": contract or "",
            "shippingConfig": account.kuehne_shipping_config or "",
            "vatConfig": account.kuehne_vat_config or "",
            "invoicingContract": account.account,
            "goodsName": account.kuehne_goods_name,
        }
        return payload

    def _kuehne_get_line_number(self):
        """Get the number of lines of the deposit slip.
        @returns int
        """
        self.ensure_one()
        lines = 13
        for picking in self.picking_ids:
            lines += len(picking.kuehne_meta.split("\n"))
            lines += len(picking.kuehne_meta_footer.split("\n"))
            lines += len(picking._get_packages_from_picking())
        return lines

    def _kuehne_create_edi_lines(self):
        """Create lines for each picking.
        The carrier is expecting a line per shipping.
        @returns []
        """
        self.ensure_one()
        lines = []
        for picking in self.picking_ids:
            lines.append(picking.kuehne_get_meta())
        return lines

    def _kuehne_create_edi_file(self):
        """Create a .txt file with headers and data.
        params:
            data : [OrderedDict]
        return: io.ByteIO
        """
        payload = self._kuehne_prepare_edi_payload()
        edi_file = roulier.get(self.delivery_type, "get_edi", payload)
        return edi_file

    def _kuehne_create_attachment(self):
        """Create a slip and add it in attachment."""
        edi_file = self._kuehne_create_edi_file()
        vals = {
            "name": self.name + ".txt",
            "res_id": self.id,
            "res_model": "deposit.slip",
            "datas": b64encode(edi_file.encode("utf-8")),
            "type": "binary",
            "task_id": self.env.ref(
                "delivery_roulier_kuehne_nagel_fr.kuehne_export_deposit_task"
            ).id,
            "file_type": "export",
        }
        return self.env["attachment.queue"].create(vals)

    def create_edi_file(self):
        self.ensure_one()
        if self.delivery_type == "kuehne_nagel_fr" and self.picking_ids:
            return self._kuehne_create_attachment()
        else:
            return super().create_edi_file()
