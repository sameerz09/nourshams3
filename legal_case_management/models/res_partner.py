# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """Inherit res partner"""
    _inherit = 'res.partner'

    is_judge = fields.Boolean(string='Is Judge', help='Is he a Judge')
    is_judge_unavailable = fields.Boolean(string="Judge Available?",
                                          default=False,
                                          help="Check the availability of judge")

    mobile2 = fields.Char(string='Mobile')

    full_name = fields.Char(string="Full Name")
    family_name = fields.Char(string="Family Name", help="The family name of the partner.")
    card_id = fields.Char(string="Card ID", help="Identification card number.")
    representative_name = fields.Char(string="Representative Name", help="The agent representing the partner.")

    @api.onchange('mobile2')
    def _onchange_mobile2(self):
        """Update mobile when mobile2 is changed."""
        for rec in self:
            rec.mobile = rec.mobile2

    @api.constrains('mobile2')
    def _check_mobile2_format(self):
        for rec in self:
            if rec.mobile2:
                if not rec.mobile2.isdigit():
                    raise ValidationError(_("Mobile 2 must contain only digits."))
                if len(rec.mobile2) != 10:
                    raise ValidationError(_("Mobile 2 must be exactly 10 digits long."))

    @api.onchange('full_name')
    def _onchange_full_name(self):
        """Update name when full_name is changed."""
        for rec in self:
            rec.name = rec.full_name
