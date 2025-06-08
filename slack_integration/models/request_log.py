from odoo import models, fields, api

class RequestLog(models.Model):
    _name = 'request.log'
    _description = 'Request Log'

    name = fields.Char(string="Name", required=True)
    headers = fields.Text(string="Headers")
    query_params = fields.Text(string="Query Parameters")
    body = fields.Text(string="Body")
    create_date = fields.Datetime(string="Request Date", readonly=True, default=fields.Datetime.now)
