# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AttachmentSynchronizeTask(models.Model):
    _inherit = "attachment.synchronize.task"

    file_type = fields.Selection(
        selection_add=[
            ("import_directional_code", "Import Kuehne Nagel Directional Codes")
        ]
    )
