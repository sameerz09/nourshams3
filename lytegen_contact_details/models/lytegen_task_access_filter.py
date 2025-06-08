from odoo import models, api
from datetime import datetime, timedelta

class TaskAccessFilter(models.Model):
    _inherit = 'project.task'

    @api.model
    def web_search_read(self, domain, offset=0, limit=None, order=None, **kwargs):
        if self.env.user.has_group('lytegen_contact_details.group_sales_consultant'):
            domain = domain + [
                '|',
                ('user_ids', 'in', [self.env.uid]),
                ('create_uid', '=', self.env.uid)
            ]
            print('Access filter applied for FSM user')

        return super().web_search_read(domain, offset=offset, limit=limit, order=order, **kwargs)
