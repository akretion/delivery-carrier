# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2016 Akretion (https://www.akretion.com).
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          Sébastien BEAU
##############################################################################

from openerp import models, fields, api
import base64
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
import unicodecsv


class KuehneDirectionalCode(models.Model):
    _name = 'kuehne.directional.code'

    _rec_name = 'city_to'

    start_date = fields.Date(
        "Start date",
        help="Code valid from this date",
    )
    office_from = fields.Char('Start office')
    country_from_id = fields.Many2one(
        comodel_name='res.country',
        string='Country From'
    )
    country_to_id = fields.Many2one(
        comodel_name='res.country',
        string='Country To'
    )
    city_to = fields.Char('City To')
    first_zip = fields.Char('First Zip')
    last_zip = fields.Char('Last Zip')
    first_city_code = fields.Char()
    last_city_code = fields.Char()
    office_code = fields.Char()
    office_round = fields.Char()
    export_hub = fields.Char()

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = "%s - %s %s %s" % (
                record.country_to_id.code, record.city_to, record.first_zip,
                record.last_zip)
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        if self._context.get('company_id'):
            company = self.env['res.company'].browse(
                self._context['company_id'])
            args.append(['country_from_id', '=', company.country_id.id])
        if self._context.get('partner_shipping_id'):
            partner = self.env['res.partner'].browse(
                self._context['partner_shipping_id'])
            args += [
                ['country_to_id', '=', partner.country_id.id],
                '|',
                ['city_to', '=', partner.city.upper()],
                '&',
                ['first_zip', '<=', partner.zip],
                ['last_zip', '>=', partner.zip]]
        results = super(KuehneDirectionalCode, self).name_search(
            name, args=args, operator=operator, limit=limit)
        return results

    @api.model
    def _search_directional_code(
            self, country_from, country_to, zip_code, city):
        directional_code = False
        directional_codes = self.search([
            ('start_date', '<=', fields.Date.today()),
            ('country_from_id', '=', country_from),
            ('country_to_id', '=', country_to),
            ('first_zip', '<=', zip_code),
            ('last_zip', '>=', zip_code)
        ])
        if directional_codes:
            if len(directional_codes) == 1:
                directional_code = directional_codes
            else:
                for code in directional_codes:
                    conv_city = city.upper().replace("'", ' ')
                    if code.city_to == conv_city:
                        directional_code = code
        else:
            first_zip_state = '%s000' % zip_code[:2]
            last_zip_state = '%s999' % zip_code[:2]
            directional_codes = self.search([
                ('start_date', '<=', fields.Date.today()),
                ('country_from_id', '=', country_from),
                ('country_to_id', '=', country_to),
                ('first_zip', '>=', first_zip_state),
                ('last_zip', '<=', last_zip_state),
                ('city_to', '=', city.upper().replace("'", ' '))
            ])
            if len(directional_codes) == 1:
                directional_code = directional_codes
        return directional_code

    @api.model
    def import_directional_code(self, data):
        str_io = StringIO()
        str_io.writelines(base64.b64decode(data))
        str_io.seek(0)
        fields = [
            'start_date', 'office_from', 'country_from', 'country_to',
            'city_to', 'first_zip', 'last_zip', 'first_city_code',
            'last_city_code', 'office_code', 'office_round', 'export_hub']
        reader = unicodecsv.DictReader(
            str_io, fieldnames=fields,
            encoding="ISO-8859-15", delimiter=';')
        for row in reader:
            country_from = self.env['res.country'].search(
                [('code', '=', row['country_from'].lower())])
            country_to = self.env['res.country'].search(
                [('code', '=', row['country_to'].lower())])
            directional_code = self.search([
                ('office_from', '=', row['office_from']),
                ('country_from_id', '=', country_from.id),
                ('country_to_id', '=', country_to.id),
                ('city_to', '=', row['city_to']),
                ('first_zip', '=', row['first_zip']),
                ('last_zip', '=', row['last_zip']),
                ('first_city_code', '=', row['first_city_code']),
                ('last_city_code', '=', row['last_city_code'])
            ])
            if directional_code:
                directional_code.write({
                    'start_date': row['start_date'],
                    'office_code': row['office_code'],
                    'office_round': row['office_round'],
                    'export_hub': row['export_hub']
                })
            else:
                vals = {
                    'start_date': row['start_date'],
                    'office_from': row['office_from'],
                    'country_from_id': country_from.id,
                    'country_to_id': country_to.id,
                    'city_to': row['city_to'],
                    'first_zip': row['first_zip'],
                    'last_zip': row['last_zip'],
                    'first_city_code': row['first_city_code'],
                    'last_city_code': row['last_city_code'],
                    'office_code': row['office_code'],
                    'office_round': row['office_round'],
                    'export_hub': row['export_hub']
                }
                self.create(vals)
        return True


class IrAttachmentMetadata(models.Model):
    _inherit = 'ir.attachment.metadata'

    file_type = fields.Selection(
        selection_add=[
            ('import_directional_code',
             'Import Kuehne Nagel Directional Codes')
        ])

    @api.multi
    def _run(self):
        super(IrAttachmentMetadata, self)._run()
        if self.file_type == 'import_directional_code':
            self.env['kuehne.directional.code'].import_directional_code(
                self.datas)


class Task(models.Model):
    _inherit = 'external.file.task'

    file_type = fields.Selection(
        selection_add=[
            ('import_directional_code',
             'Import Kuehne Nagel Directional Codes')
        ])
