# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import csv
from io import StringIO

from odoo import api, fields, models


class KuehneDirectionalCode(models.Model):
    _name = "kuehne.directional.code"
    _description = "Kuehne Directional Codes"

    _rec_name = "city_to"

    start_date = fields.Date(
        help="Code valid from this date",
    )
    office_from = fields.Char("Start office")
    country_from_id = fields.Many2one(comodel_name="res.country", string="Country From")
    country_to_id = fields.Many2one(comodel_name="res.country", string="Country To")
    city_to = fields.Char(index=True)
    first_zip = fields.Char()
    last_zip = fields.Char()
    first_city_code = fields.Char()
    last_city_code = fields.Char()
    office_code = fields.Char()
    office_round = fields.Char()
    export_hub = fields.Char()

    def name_get(self):
        res = []
        for record in self:
            name = "%s - %s %s %s" % (
                record.country_to_id.code,
                record.city_to,
                record.first_zip,
                record.last_zip,
            )
            res.append((record.id, name))
        return res

    @api.model
    def convert_city_name(self, city):
        return (
            city
            and city.upper()
            .replace("'", " ")
            .replace("-", " ")
            .replace(" CEDEX", "")
            .replace("SAINT ", "ST ")
            .replace("É", "E")
            .replace("È", "E")
            .replace("À", "A")
            .replace("’", " ")
            or city
        )

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=80):
        # TODO check if usefull / Check if we need to replace by self.env.company (always true)
        if self._context.get("company_id"):
            company = self.env["res.company"].browse(self._context["company_id"])
            args.append(["country_from_id", "=", company.country_id.id])
        if self._context.get("partner_shipping_id"):
            partner = self.env["res.partner"].browse(
                self._context["partner_shipping_id"]
            )
            city = self.convert_city_name(partner.city)
            args += [
                ["country_to_id", "=", partner.country_id.id],
                "|",
                ["city_to", "=", city],
                "&",
                ["first_zip", "<=", partner.zip],
                ["last_zip", ">=", partner.zip],
            ]
        results = super().name_search(name, args=args, operator=operator, limit=limit)
        return results

    @api.model
    def _search_directional_code(self, country_from, country_to, zip_code, city):
        directional_code = False
        directional_codes = self.search(
            [
                ("start_date", "<=", fields.Date.today()),
                ("country_from_id", "=", country_from),
                ("country_to_id", "=", country_to),
                ("first_zip", "<=", zip_code),
                ("last_zip", ">=", zip_code),
            ]
        )
        if directional_codes:
            if len(directional_codes) == 1:
                directional_code = directional_codes
            else:
                for code in directional_codes:
                    conv_city = self.convert_city_name(city)
                    if code.city_to == conv_city:
                        directional_code = code
        else:
            first_zip_state = "%s000" % zip_code[:2]
            last_zip_state = "%s999" % zip_code[:2]
            city = self.convert_city_name(city)
            directional_codes = self.search(
                [
                    ("start_date", "<=", fields.Date.today()),
                    ("country_from_id", "=", country_from),
                    ("country_to_id", "=", country_to),
                    ("first_zip", ">=", first_zip_state),
                    ("last_zip", "<=", last_zip_state),
                    ("city_to", "=", city),
                ]
            )
            if len(directional_codes) == 1:
                directional_code = directional_codes
        return directional_code

    @api.model
    def import_directional_code(self, data):
        str_io = StringIO()
        str_io.writelines(base64.b64decode(data).decode("ISO-8859-15"))
        str_io.seek(0)
        fields = [
            "start_date",
            "office_from",
            "country_from",
            "country_to",
            "city_to",
            "first_zip",
            "last_zip",
            "first_city_code",
            "last_city_code",
            "office_code",
            "office_round",
            "export_hub",
        ]
        reader = csv.DictReader(str_io, fieldnames=fields, delimiter=";")
        for row in reader:
            country_from = self.env["res.country"].search(
                [("code", "=", row["country_from"])]
            )
            country_to = self.env["res.country"].search(
                [("code", "=", row["country_to"])]
            )
            directional_code = self.search(
                [
                    ("office_from", "=", row["office_from"]),
                    ("country_from_id", "=", country_from.id),
                    ("country_to_id", "=", country_to.id),
                    ("city_to", "=", row["city_to"]),
                    ("first_zip", "=", row["first_zip"]),
                    ("last_zip", "=", row["last_zip"]),
                    ("first_city_code", "=", row["first_city_code"]),
                    ("last_city_code", "=", row["last_city_code"]),
                ]
            )
            if directional_code:
                directional_code.write(
                    {
                        "start_date": row["start_date"],
                        "office_code": row["office_code"],
                        "office_round": row["office_round"],
                        "export_hub": row["export_hub"],
                    }
                )
            else:
                vals = {
                    "start_date": row["start_date"],
                    "office_from": row["office_from"],
                    "country_from_id": country_from.id,
                    "country_to_id": country_to.id,
                    "city_to": row["city_to"],
                    "first_zip": row["first_zip"],
                    "last_zip": row["last_zip"],
                    "first_city_code": row["first_city_code"],
                    "last_city_code": row["last_city_code"],
                    "office_code": row["office_code"],
                    "office_round": row["office_round"],
                    "export_hub": row["export_hub"],
                }
                self.create(vals)
        return True
