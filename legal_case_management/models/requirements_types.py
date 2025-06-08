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


class RequirementsTypes(models.Model):
    """Case registration and invoice for trials and case"""
    _name = 'requirements.types'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Requirements Types'
    name = fields.Char(string="Requirement Name")
    requirement_name = fields.Char(string="Requirement Name")
    requirements_code = fields.Char(string="Requirement Code", required=True)
    req_vio_id = fields.Many2one('violations.types', string="Requirement Violation")
    case_id = fields.Many2one('case.registration', string="Related Case")  # New: Links to case registration
    is_yes = fields.Boolean(string="Yes", default=False, tracking=True)


    # _sql_constraints = [
    #     ('unique_requirements_code', 'unique(requirements_code)', 'Requirement Code must be unique!')
    # ]


    # violation_code = fields.Char(string="Violation Code")


