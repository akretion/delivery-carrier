# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Chafique DELLI <chafique.delli@akretion.com>
#    Copyright 2014 Akretion
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api


class res_partner(models.Model):
    _inherit = "res.partner"

    use_b2c_info = fields.Boolean(
       'Advanced address',
       help="Display additional information for home delivery (b2c)")
    door_code = fields.Char(
       'Door Code')
    door_code2 = fields.Char(
       'Door Code 2',)
    intercom = fields.Char(
       'Intercom',
       help="Informations for Intercom such as name "
            "or number on the intercom")
    housing_type = fields.Selection(
        selection=[
            ('house', 'House'),
            ('appartment', 'Appartment'),
            ('business_premises', 'Business premises'),
            ('other', 'Other'),
        ],
    )
    housing_access = fields.Selection(
        selection=[
            ('elevator', 'Elevator'),
            ('stairs', 'Stairs'),
            ('both', 'Elevator and stairs'),
        ],
    )
    floor = fields.Char()
