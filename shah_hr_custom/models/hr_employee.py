# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
#________________________________________________ Model Inherit

class hr_attendance(models.Model):
    _inherit = 'hr.employee'

    attendance_id = fields.Many2one(comodel_name="hr.attendance.structure", string="Attendance Rule", required=False, )

    # senior_id = fields.Many2one(comodel_name="hr.employee", string="Senior", required=False, )
    # street = fields.Char(string="Address", required=False, )