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
#    You should have received a copy  the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.of
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ViolationsTypes(models.Model):
    """Case registration and invoice for trials and case"""
    _name = 'violations.types'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Violations Types'

    violation_name = fields.Char(string="Violation Name")
    name = fields.Char(string="Violation Name")
    # violation_code = fields.Char(string="Violation Code")


