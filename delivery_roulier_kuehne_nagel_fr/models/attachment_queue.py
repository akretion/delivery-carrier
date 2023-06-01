# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AttachmentQueue(models.Model):
    _inherit = "attachment.queue"

    file_type = fields.Selection(
        selection_add=[
            ("import_directional_code", "Import Kuehne Nagel Directional Codes")
        ]
    )

    def _run(self):
        res = super()._run()
        if self.file_type == "import_directional_code":
            self.env["kuehne.directional.code"].import_directional_code(self.datas)
        return res
