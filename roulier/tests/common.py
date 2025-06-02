# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from unittest.mock import patch
from roulier import roulier

from odoo.tests import common


class RoulierCommonCase(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._roulier_all_carriers = roulier.get_carriers_action_available()
        cls._roulier_carriers = [
            carrier
            for carrier, actions in cls._roulier_all_carriers.items()
            if set(("get_metadata", "get_label")) <= set(actions)
        ]
        cls._roulier_metadata = {
            carrier: roulier.get(carrier, "get_metadata", None)
            for carrier in cls._roulier_carriers
        }


class RoulierColissimoPatchedCase(RoulierCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.account = cls.env["carrier.account"].create(
            {
                "name": "Colissimo",
                "delivery_type": "colissimo_fr",
                "account": "colissimo_account",
                "password": "colissimo_password",
            }
        )
        cls.account.roulier_properties = {
            "labelformat": "DPL_10x15_203dpi_UL",
            "customerid": "123456789",
        }
        cls.delivery = cls.account.delivery_carrier_ids.filtered(
            lambda d: d.code == "DOM"
        )
        cls.packaging = cls.env["stock.package.type"].create(
            {
                "name": "Colissimo Packaging",
                "barcode": "cbox",
                "packaging_length": 20.0,
                "width": 15.0,
                "height": 10.0,
                "max_weight": 500.0,
            }
        )
        cls.delivery.roulier_properties = {
            "default_packaging_id": cls.packaging.id,
        }

        def patched_request(method, json=None, url=None):
            if method == "generateLabel":
                return {"json": json}
            raise ValueError(f"Unexpected method: {method}")

        def patched_parse_response(response):
            if "json" in response:
                return {
                    "<jsonInfos>": {
                        "messages": [
                            {
                                "id": "0",
                                "type": "INFOS",
                                "messageContent": "La requête a été traitée avec succès",
                                "replacementValues": [],
                            }
                        ],
                        "labelXmlV2Reponse": None,
                        "labelV2Response": {
                            "parcelNumber": "TRACKING_NUMBER",
                            "parcelNumberPartner": "TRACKING_PARTNER",
                            "pdfUrl": None,
                        },
                    },
                    # Put the JSON request in the output label
                    "<label>": json.dumps(response["json"]).encode("utf-8"),
                }
            raise ValueError("Invalid response format")

        cls.patches = [
            patch(
                "roulier.carriers.colissimo_fr.carrier.ColissimoFr.validate",
            ),
            patch(
                "roulier.carriers.colissimo_fr.carrier.ColissimoFr.request",
                side_effect=patched_request,
            ),
            patch(
                "roulier.carriers.colissimo_fr.carrier.ColissimoFr._parse_response",
                side_effect=patched_parse_response,
            ),
        ]
        for p in cls.patches:
            p.start()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        for p in cls.patches:
            p.stop()

    def _get_request(self, fake_label):
        return json.loads(fake_label.decode("utf-8")) if fake_label else None
