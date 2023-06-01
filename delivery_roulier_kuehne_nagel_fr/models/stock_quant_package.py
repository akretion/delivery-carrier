##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2016 Akretion (https://www.akretion.com).
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          Sébastien BEAU
##############################################################################

from odoo import models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    #    kuehne_meta = fields.Text(
    #        "meta",
    #        help="Needed for deposit slip",
    #    )

    def _kuehne_nagel_fr_get_tracking_link(self):
        return self.url

    def _kuehne_nagel_fr_get_parcels(self, picking):
        vals_list = self._roulier_get_parcels(picking)
        package_count = len(vals_list)
        package_volume = round(picking.volume / package_count, 2)
        for vals in vals_list:
            vals["volume"] = package_volume
        return vals_list


#    def kuehne_get_meta(self):
#        return "\n".join([pack.kuehne_meta for pack in self])
