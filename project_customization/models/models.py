from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError, AccessError
import requests
import json
import logging
from datetime import datetime, timedelta
from datetime import date
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import traceback

_logger = logging.getLogger(__name__)

class ProjectFile(models.Model):
    _name = 'project.file'
    _description = 'Project File'

    name = fields.Char(string="File Name", required=True)
    file = fields.Binary(string="File", required=True)
    project_id = fields.Many2one('project.project', string="Project", ondelete="cascade")


class ProjectProject(models.Model):
    _inherit = 'project.project'

    date_of_birth = fields.Date(string="تاريخ الميلاد")

    displacement_reasons = fields.Selection([
        ('house_demolition', 'هدم المنزل'),
        ('direct_bombing', 'قصف مباشر'),
        ('arrest_threat', 'تهديد بالاعتقال'),
        ('job_loss', 'فقدان العمل'),
        ('lack_services', 'انعدام الخدمات'),
    ], string="أسباب النزوح", help="اختر سبب أو أكثر", required=False)

    displacement_residence_type = fields.Selection([
        ('shelter', 'مركز إيواء'),
        ('relatives', 'لدى أقارب'),
        ('rented', 'شقة مستأجرة'),
        ('partial_return', 'عائد للمنزل لكن جزء من الأسرة ما زال نازحًا'),
        ('other', 'موقع آخر')
    ], string="مكان الإقامة الحالي", tracking=True)

    multiple_displacements = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل تعرضتم لأكثر من حالة تهجير؟", tracking=True)

    sales_consultant_employee_id = fields.Many2one(
        'hr.employee',
        string="Sales Consultant (Employee)",
        domain=lambda self: self._default_domain_sales_consultant_employee(),
        help="Sales Consultant assigned to this event (Employee)."
    )

    # sales_consultant_employee_id = fields.Many2one(
    #     'hr.employee',
    #     string="Sales Consultant (Employee)",
    #     domain=lambda self: self._default_domain_sales_consultant_employee(),
    #     help="Sales Consultant assigned to this project."
    # )

    displacement_date = fields.Date(string="تاريخ النزوح", tracking=True)
    request_date = fields.Datetime(string="تاريخ تقييد الطلب", default=lambda self: fields.Datetime.now(),
                                   tracking=True)
    customer_name = fields.Char(string="Customer Name", required=True, tracking=True)
    phone = fields.Char(string="Phone", required=True, tracking=True)
    email = fields.Char(string="Email", required=True, tracking=True)
    secondary_customer_name = fields.Char(string="Secondary Customer Name", tracking=True)
    secondary_phone = fields.Char(string="Secondary Phone", tracking=True)
    secondary_email = fields.Char(string="Secondary Email", tracking=True)
    street_address = fields.Text(string="Street Address", required=True, tracking=True)
    city = fields.Char(string="City", required=False, tracking=True)
    state = fields.Char(string="State", required=False, tracking=True)
    zip_code = fields.Char(string="Zip Code", required=False, tracking=True)
    reroof = fields.Selection([
        ('yes_needed', 'Yes Needed'),
        ('yes_customer_requested', 'Yes Customer Requested'),
        ('not_needed', 'Not Needed')],
        string="Reroof", required=True, tracking=True
    )
    mount = fields.Selection([
        ('roof', 'Roof'),
        ('ground', 'Ground'),
        ('mixed', 'Mixed')],
        string="Mount", required=True, tracking=True
    )
    hoa = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],
        string="HOA", required=True, tracking=True
    )
    gated_access = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],
        string="Gated Access", required=True, tracking=True
    )
    gate_code = fields.Char(string="Gate Code", required=False, tracking=True)

    battery = fields.Selection([
        ('grid_tied', 'Grid-Tied'),
        ('full_backup', 'Full BackUp'),
        ('no_battery', 'No Battery')],
        string="Battery", required=True, tracking=True
    )
    utility_bill_holder = fields.Selection([
        ('customer', 'Customer'),
        ('cosigner_on_contract', 'Cosigner on Contract'),
        ('other', 'Other')],
        string="Utility Bill Holder", required=True, tracking=True
    )
    other_utility_bill_holder = fields.Char(string="Other Utility Bill Holder", required=False, tracking=True)
    provider = fields.Char(string="Provider", required=True, tracking=True)
    finance_type = fields.Selection([
        ('loan', 'Loan'),
        ('ppa', 'PPA'),
        ('cash', 'Cash'),
        ('enfin_loan', 'Enfin Loan'),
        ('everbright_loan', 'Everbright Loan'),
        ('goodleap_ppa', 'GoodLeap PPA'),
        ('goodleap_loan', 'GoodLeap Loan'),
        ('lightreach_ppa', 'Lightreach PPA'),
        ('mosaic_loan', 'Mosaic Loan'),
        ('pace', 'PACE'),
        ('sunlight_loan', 'Sunlight Loan'),
        ('sunrun_ppa', 'Sunrun PPA'),
        ('thrive_ppa', 'Thrive PPA')],
        string="Finance Type", required=True, tracking=True
    )
    loantype = fields.Char(string="Loan Type", required=False, tracking=True)
    installer = fields.Selection([
        ('lytegen', 'Lytegen'),
        ('brightops', 'BrightOps'),
        ('thrive', 'Thrive')],
        string="Installer", required=False, tracking=True
    )
    lead_origin = fields.Selection([
        ('company_lead', 'Company Lead'),
        ('company_referral', 'Company Referral'),
        ('selfgen', 'Selfgen')],
        string="Lead Origin", required=True, tracking=True
    )
    requested_site_survey_date = fields.Selection([
        ('soonest_possible', 'Soonest Possible - FASTEST INSTALL'),
        ('custom_requested', 'Custom Requested')],
        string="Requested Site Survey Date", required=True, tracking=True
    )
    custom_ss_times = fields.Text(string="Custom SS Times", required=True, tracking=True)
    usage_files = fields.Many2many(
        'ir.attachment',
        relation="project_usage_files_rel",
        string="صورة الهوية",
        tracking=True
    )
    additional_files = fields.Many2many(
        'ir.attachment',
        relation="project_additional_files_rel",
        string=" صور لموقع الإقامة الحالي",
        tracking=True
    )

    unrwa_document = fields.Many2many(
        'ir.attachment',
        relation="project_unrwa_document_rel",
        string="وثيقة الأونروا",
        tracking=True
    )

    family_member_count = fields.Integer(string="عدد أفراد العائلة", tracking=True)

    notes = fields.Text(
        string="Notes / Special Requests",
        help="Help us understand this project completely and give as much detail as possible",
        required=True,
        tracking=True
    )
    special_request = fields.Text(string="Special Request", help="If no special request, put 'NA'", tracking=True)
    system_size = fields.Float(string="System Size", required=True, tracking=True)
    project_id = fields.Char(string="Project ID", tracking=True)
    installer_id = fields.Char(string="Installer ID", tracking=True)
    last_contact = fields.Date(string="Last Contact", tracking=True)
    last_bps_update = fields.Datetime(string="Last BPS Update", tracking=True)
    project_status = fields.Char(string="Project Status", tracking=True)
    funding_source = fields.Char(string="Funding Source", tracking=True)
    funding_kickback = fields.Char(string="Funding Kickback", tracking=True)
    funding_notes = fields.Text(string="Funding Notes", tracking=True)
    sales_action = fields.Char(string="Sales Action", tracking=True)
    sales_action_notes = fields.Text(string="Sales Action Notes", tracking=True)
    site_survey_scheduled = fields.Date(string="Site Survey Scheduled", tracking=True)
    ss_completed = fields.Date(string="Site Survey Completed", tracking=True)
    installation_scheduled = fields.Date(string="Installation Scheduled", tracking=True)
    change_order_required = fields.Date(string="Change Order Required", tracking=True)
    change_order_signed = fields.Date(string="Change Order Signed", tracking=True)
    sold_design_id = fields.Many2one(
        'design',
        string='Sold Design',
        tracking=True,
        ondelete='set null'  # Ensures if the design is deleted, the field is reset to null
    )
    street_address_visible = fields.Boolean(
        string="Is Street Address Visible",
        # compute='_compute_street_address_visible',
        default=False,
        store=True,
    )

    add_ons = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],
        string="Add Ons",
        required=True,
        tracking=True
    )

    wifi_network_id = fields.Char(
        string="WiFi Network ID",
        required=True,
        tracking=True
    )

    wifi_network_password = fields.Char(
        string="WiFi Network Password",
        required=True,
        tracking=True
    )

    electrical_update = fields.Selection([
        ('only_if_needed_fastest_install', 'Only if needed (Fastest install)'),
        ('customer_requested', 'Customer requested (45 days delay)')],
        string="Electrical Update",
        required=True,
        tracking=True
    )

    pets = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],
        string="Pets",
        required=True,
        tracking=True
    )

    create_date_formatted = fields.Char(string='Created Date/Time', compute='_compute_create_date_formatted')
    date_formatted = fields.Char(string='تاريخ انشاء الطلب', compute='_compute_date_formatted')
    time_formatted = fields.Char(string='وقت انشاء الطلب', compute='_compute_time_formatted')

    displacement_reasons = fields.Selection([
        ('forced_displacement', 'تهجير قسري'),
        ('house_demolition', 'هدم بيت'),
        ('house_damage', 'تضرر بيت'),
        ('lack_of_services', 'انعدام الخدمات'),
    ], string="أسباب النزوح", help="اختر سبب النزوح", required=False)

    displacement_residence_type = fields.Selection([
        ('shelter', 'مركز إيواء'),
        ('relatives', 'لدى أقارب'),
        ('rented', 'شقة مستأجرة'),
        ('partial_return', 'عائد للمنزل لكن جزء من الأسرة ما زال نازحًا'),
        ('other', 'موقع آخر')
    ], string="مكان الإقامة الحالي", tracking=True, required=False)

    multiple_displacements = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل تعرضتم لأكثر من حالة تهجير؟", tracking=True, required=False)

    # sales_consultant_employee_id = fields.Many2one(
    #     'hr.employee',
    #     string="Sales Consultant (Employee)",
    #     domain=lambda self: self._default_domain_sales_consultant_employee(),
    #     help="Sales Consultant assigned to this event (Employee).",
    #     required=False
    # )

    displacement_date = fields.Date(string="تاريخ النزوح", tracking=True, required=False)
    request_date = fields.Datetime(string="تاريخ تقييد الطلب", default=lambda self: fields.Datetime.now(),
                                   tracking=True, required=False)

    customer_name = fields.Char(string="Customer Name", required=False, tracking=True)
    phone = fields.Char(string="رقم الهاتف المحمول", required=False, tracking=True)
    email = fields.Char(string="الايميل", required=False, tracking=True)
    secondary_customer_name = fields.Char(string="Secondary Customer Name", tracking=True, required=False)
    secondary_phone = fields.Char(string="Secondary Phone", tracking=True, required=False)
    secondary_email = fields.Char(string="Secondary Email", tracking=True, required=False)
    street_address = fields.Text(string="Street Address", required=False, tracking=True)
    city = fields.Char(string="City", required=False, tracking=True)
    state = fields.Char(string="State", required=False, tracking=True)
    zip_code = fields.Char(string="Zip Code", required=False, tracking=True)

    reroof = fields.Selection([
        ('yes_needed', 'Yes Needed'),
        ('yes_customer_requested', 'Yes Customer Requested'),
        ('not_needed', 'Not Needed')],
        string="Reroof", required=False, tracking=True
    )

    mount = fields.Selection([
        ('roof', 'Roof'),
        ('ground', 'Ground'),
        ('mixed', 'Mixed')],
        string="Mount", required=False, tracking=True
    )

    hoa = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],
        string="HOA", required=False, tracking=True
    )

    gated_access = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],
        string="Gated Access", required=False, tracking=True
    )

    gate_code = fields.Char(string="Gate Code", required=False, tracking=True)

    battery = fields.Selection([
        ('grid_tied', 'Grid-Tied'),
        ('full_backup', 'Full BackUp'),
        ('no_battery', 'No Battery')],
        string="Battery", required=False, tracking=True
    )

    utility_bill_holder = fields.Selection([
        ('customer', 'Customer'),
        ('cosigner_on_contract', 'Cosigner on Contract'),
        ('other', 'Other')],
        string="Utility Bill Holder", required=False, tracking=True
    )

    other_utility_bill_holder = fields.Char(string="Other Utility Bill Holder", required=False, tracking=True)
    provider = fields.Char(string="Provider", required=False, tracking=True)

    finance_type = fields.Selection([
        ('loan', 'Loan'),
        ('ppa', 'PPA'),
        ('cash', 'Cash'),
        ('enfin_loan', 'Enfin Loan'),
        ('everbright_loan', 'Everbright Loan'),
        ('goodleap_ppa', 'GoodLeap PPA'),
        ('goodleap_loan', 'GoodLeap Loan'),
        ('lightreach_ppa', 'Lightreach PPA'),
        ('mosaic_loan', 'Mosaic Loan'),
        ('pace', 'PACE'),
        ('sunlight_loan', 'Sunlight Loan'),
        ('sunrun_ppa', 'Sunrun PPA'),
        ('thrive_ppa', 'Thrive PPA')],
        string="Finance Type", required=False, tracking=True
    )

    loantype = fields.Char(string="Loan Type", required=False, tracking=True)

    installer = fields.Selection([
        ('lytegen', 'Lytegen'),
        ('brightops', 'BrightOps'),
        ('thrive', 'Thrive')],
        string="Installer", required=False, tracking=True
    )

    lead_origin = fields.Selection([
        ('company_lead', 'Company Lead'),
        ('company_referral', 'Company Referral'),
        ('selfgen', 'Selfgen')],
        string="Lead Origin", required=False, tracking=True
    )

    requested_site_survey_date = fields.Selection([
        ('soonest_possible', 'Soonest Possible - FASTEST INSTALL'),
        ('custom_requested', 'Custom Requested')],
        string="Requested Site Survey Date", required=False, tracking=True
    )

    custom_ss_times = fields.Text(string="Custom SS Times", required=False, tracking=True)

    notes = fields.Text(string="Notes / Special Requests",
                        help="Help us understand this project completely and give as much detail as possible",
                        required=False, tracking=True)
    special_request = fields.Text(string="Special Request", help="If no special request, put 'NA'", tracking=True,
                                  required=False)

    system_size = fields.Float(string="System Size", required=False, tracking=True)
    project_id = fields.Char(string="Project ID", tracking=True, required=False)
    installer_id = fields.Char(string="Installer ID", tracking=True, required=False)

    last_contact = fields.Date(string="Last Contact", tracking=True, required=False)
    last_bps_update = fields.Datetime(string="Last BPS Update", tracking=True, required=False)
    project_status = fields.Char(string="Project Status", tracking=True, required=False)

    funding_source = fields.Char(string="Funding Source", tracking=True, required=False)
    funding_kickback = fields.Char(string="Funding Kickback", tracking=True, required=False)
    funding_notes = fields.Text(string="Funding Notes", tracking=True, required=False)

    sales_action = fields.Char(string="Sales Action", tracking=True, required=False)
    sales_action_notes = fields.Text(string="Sales Action Notes", tracking=True, required=False)

    site_survey_scheduled = fields.Date(string="Site Survey Scheduled", tracking=True, required=False)
    ss_completed = fields.Date(string="Site Survey Completed", tracking=True, required=False)
    installation_scheduled = fields.Date(string="Installation Scheduled", tracking=True, required=False)
    change_order_required = fields.Date(string="Change Order Required", tracking=True, required=False)
    change_order_signed = fields.Date(string="Change Order Signed", tracking=True, required=False)

    sold_design_id = fields.Many2one('design', string='Sold Design', tracking=True, ondelete='set null', required=False)

    street_address_visible = fields.Boolean(string="Is Street Address Visible", default=False, store=True)

    add_ons = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],
        string="Add Ons", required=False, tracking=True
    )

    wifi_network_id = fields.Char(string="WiFi Network ID", required=False, tracking=True)
    wifi_network_password = fields.Char(string="WiFi Network Password", required=False, tracking=True)

    electrical_update = fields.Selection([
        ('only_if_needed_fastest_install', 'Only if needed (Fastest install)'),
        ('customer_requested', 'Customer requested (45 days delay)')],
        string="Electrical Update", required=False, tracking=True
    )

    pets = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],
        string="Pets", required=False, tracking=True
    )

    create_date_formatted = fields.Char(string='Created Date/Time', compute='_compute_create_date_formatted')
    date_formatted = fields.Char(string='Created Date/Time', compute='_compute_date_formatted')
    time_formatted = fields.Char(string='Created Date/Time', compute='_compute_time_formatted')

    id_number = fields.Char(string="رقم الهوية", required=True)
    unrwa_card_number = fields.Char(string="رقم كرت UNRWA", required=True)
    family_member_count = fields.Integer(string="عدد أفراد العائلة", required=True)
    is_currently_displaced = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل الأسرة نازحة حاليًا؟", required=True)

    pre_displacement_area = fields.Char(string="مكان السكن قبل النزوح", required=True)
    post_displacement_area_options = [
        ('tulkarem', 'طولكرم'),
        ('ektaba', 'اكتابا'),
        ('thanaba', 'ذنابه'),
        ('salem_neighborhood', 'حارة السلام'),
        ('alzoub', 'العزب'),
        ('anabta', 'عنبتا'),
        ('balaa', 'بلعا'),
        ('shuweika', 'شويكه'),
        ('kafr_labad', 'كفر اللبد'),
        ('deir_ghassoun', 'دير الغصون'),
        ('attil', 'عتيل'),
        ('other', 'اخرى / حدد'),
    ]

    post_displacement_area_selections = fields.Selection(
        selection=post_displacement_area_options,
        string="العنوان الحالي بعد النزوح"
    )

    post_displacement_area = fields.Char(string="العنوان الحالي بعد النزوح", required=True)

    housing_type = fields.Selection([
        ('inside_camp', 'بيت داخل المخيم'),
        ('outside_camp', 'بيت خارج المخيم'),
        ('with_relatives', 'عند أقارب'),
        ('shelter_center', 'مركز إيواء (مدرسة أو مسجد…)'),
        ('no_fixed_housing', 'بدون سكن ثابت'),
    ], string="نوع السكن الحالي", required=True)

    housing_damage_level = fields.Selection([
        ('none', 'لا'),
        ('minor', 'بسيط'),
        ('moderate', 'متوسط'),
        ('destroyed', 'دمار كلي'),
    ], string="تعرض السكن لأضرار؟", required=True)

    damage_documented = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل تم توثيق الضرر؟", required=True)

    economic_status = fields.Selection([
        ('pension', 'راتب تقاعدي'),
        ('no_income', 'لا دخل'),
        ('aid_only', 'مساعدات فقط'),
        ('one_working', 'شخص واحد يعمل'),
        ('multiple_working', 'أكثر من شخص يعمل'),
    ], string="وضع الأسرة الاقتصادي الحالي", required=True)


    worked_inside_palestine_before = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل كان يعمل أحد داخل فلسطين قبل النزوح؟", required=True)

    workers_count_before_displacement = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3_plus', '3+'),
    ], string="عدد من كانوا يعملون", required=False)

    has_unemployed = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل يوجد عاطلون؟", required=True)
    has_school_students = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل في الأسرة طلاب مدارس؟", required=True)

    school_attendance_status = fields.Selection([
        ('all_continuing', 'مستمرون'),
        ('some_stopped', 'بعضهم توقف'),
    ], string="وضع طلاب المدارس", required=False)

    has_university_students = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="طلاب جامعات؟", required=True)

    university_attendance_status = fields.Selection([
        ('continuing', 'التعليم مستمر'),
        ('stopped', 'توقف'),
    ], string="وضع طلاب الجامعات", required=False)

    has_disabled_members = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل في الأسرة ذوي إعاقة؟", required=False)

    disabled_count = fields.Integer(string="عدد ذوي الإعاقة", required=False)

    disability_type = fields.Selection([
        ('visual', 'الإعاقة البصرية'),
        ('hearing', 'الإعاقة السمعية'),
        ('speech', 'الإعاقة النطقية'),
        ('mental', 'الإعاقة العقلية'),
        ('physical', 'الإعاقة الجسمية والحركية'),
        ('chronic', 'مرض مزمن'),
    ], string="نوع الإعاقة", required=False)

    receiving_care = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل يتلقون رعاية؟", required=False)

    care_affected_by_displacement = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل تأثرت الرعاية بالنزوح؟", required=False)

    basic_needs = fields.Selection([
        ('shelter', 'مسكن'),
        ('food', 'غذاء'),
        ('treatment', 'علاج'),
        ('clothing', 'ملابس'),
        ('financial_aid', 'مساعدات مالية'),
        ('baby_supplies', 'مستلزمات أطفال'),
        ('support', 'دعم تعليمي/نفسي/لذوي الإعاقة'),
        ('other', 'أخرى'),
    ], string="الاحتياجات الأساسية", required=False)

    data_sharing_consent = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل توافق على مشاركة البيانات؟", required=True)

    additional_notes = fields.Text(string="ملاحظات إضافية")

    house_damage_photos = fields.Many2many(
        'ir.attachment',
        relation="project_house_damage_photos_rel",
        string="صور أضرار البيت",
        tracking=True
    )

    report_documents = fields.Many2many(
        'ir.attachment',
        relation="project_report_documents_rel",
        string="تقارير طبية",
        tracking=True
    )
    family_skills = fields.Selection([
        ('construction', 'بناء'),
        ('electricity', 'كهرباء'),
        ('education', 'تعليم'),
        ('maintenance', 'صيانة'),
        ('other', 'آخر'),
    ], string="مهارات يتقنها أفراد العائلة", required=False)

    pre_displacement_address = fields.Text(string="العنوان الكامل قبل النزوح")
    pre_displacement_house_type = fields.Selection([
        ('independent', 'بيت مستقل'),
        ('apartment', 'شقة'),
        ('shared_building', 'بناية مشتركة'),
    ], string="نوع البيت")

    pre_displacement_floors = fields.Integer(string="عدد الطوابق")
    pre_displacement_rooms = fields.Integer(string="عدد الغرف")

    house_ownership_status = fields.Selection([
        ('owned', 'ملك'),
        ('rented', 'مستأجر'),
    ], string="هل كان ملكاً أم مستأجراً؟")

    shared_with = fields.Char(string="من كان يقطن معكم؟ (عدد الأسر، الأفراد)")
    other_families_on_floor = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل كان في الطابق سكّان غيركم؟")

    pre_displacement_description = fields.Text(string="وصف موجز للموقع")

    housing_condition = fields.Selection([
        ('habitable', 'صالح للسكن'),
        ('uninhabitable', 'غير صالح'),
    ], string="حالة السكن")

    employment_type = fields.Selection([
        ('gov', 'موظف حكومي'),
        ('agency', 'موظف وكالة'),
        ('private', 'قطاع خاص'),
        ('interior_worker', 'عامل في الداخل'),
    ], string="طبيعة العمل")

    stable_income = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل يوجد مصدر دخل ثابت؟")

    interior_workers = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل يوجد عمال في الداخل؟")

    can_still_work = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل لا يزالون قادرين على العمل؟")

    lost_shop = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل فقدتم محلاً تجارياً؟")

    shop_name = fields.Char(string="اسم المحل")
    shop_location = fields.Char(string="موقع المحل")
    shop_business_type = fields.Char(string="نوع العمل")
    shop_ownership = fields.Selection([
        ('owned', 'ملك'),
        ('rented', 'مستأجر'),
    ], string="ملك أم مستأجر")

    shop_main_income_source = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل كان مصدر الدخل الأساسي؟")

    workers_count = fields.Integer(string="عددهم")

    has_family_martyr = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل يوجد شهيد؟", tracking=True)

    has_family_prisoner = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل يوجد أسير؟", tracking=True)

    has_family_injured = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل يوجد جريح؟", tracking=True)

    martyr_name = fields.Char(string="الاسم الكامل")
    relation_to_head = fields.Char(string="العلاقة برب الأسرة")
    event_date = fields.Date(string="تاريخ الحدث")
    event_details = fields.Text(string="تفاصيل إضافية")

    has_special_equipment = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل لديكم أدوات أو معدات متخصصة؟")

    interested_in_self_employment = fields.Selection([
        ('yes', 'نعم'),
        ('no', 'لا'),
    ], string="هل ترغبون في مشاريع تشغيل ذاتي؟")

    medical_report_file = fields.Binary(string="ملف طبي/توثيقي")
    medical_report_filename = fields.Char(string="اسم الملف")

    wife_full_name = fields.Char(string="اسم الزوجة الرباعي")
    wife_id_number = fields.Char(string="رقم هوية الزوجة")

    skill_construction = fields.Boolean(string="بناء")
    skill_electricity = fields.Boolean(string="كهرباء")
    skill_education = fields.Boolean(string="تعليم")
    skill_maintenance = fields.Boolean(string="صيانة")
    skill_other = fields.Boolean(string="آخر")

    age = fields.Integer(string="العمر", compute='_compute_age', store=True)

    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth:
                today = date.today()
                dob = record.date_of_birth
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                record.age = age
            else:
                record.age = 0



    def unlink(self):
        raise ValidationError(_("غير مسموح بحذف بيانات المتضررين."))

    @api.depends('create_date')
    def _compute_create_date_formatted(self):
        for record in self:
            if record.create_date:
                # Format like "Apr-26, 2025 03:45 PM"
                record.create_date_formatted = record.create_date.strftime('%b-%d, %Y %I:%M %p')
            else:
                record.create_date_formatted = ''

    @api.model
    def web_search_read(self, domain, offset=0, limit=None, order=None, **kwargs):
        if not order or 'is_favorite' in order:
            order = 'id desc'
        return super(ProjectProject, self).web_search_read(domain, offset=offset, limit=limit, order=order, **kwargs)

    @api.depends('create_date')
    def _compute_date_formatted(self):
        for record in self:
            if record.create_date:
                # Format like "Apr-26, 2025 03:45 PM"
                record.date_formatted = record.create_date.strftime('%b-%d, %Y')
            else:
                record.date_formatted = ''

    @api.depends('create_date')
    def _compute_time_formatted(self):
        for record in self:
            if record.create_date:
                # Format like "Apr-26, 2025 03:45 PM"
                record.time_formatted = record.create_date.strftime('%I:%M %p')
            else:
                record.time_formatted = ''

    # site_survey_date1 = fields.Date(string="Requested site survey dates 1", required=True, tracking=True)
    # site_survey_date2 = fields.Date(string="Requested site survey dates 2", required=True, tracking=True)
    # site_survey_date3 = fields.Date(string="Requested site survey dates 3", required=True, tracking=True)

    design_sold = fields.Char(
        string="Design Sold",
        required=False,
        tracking=True
    )



    @api.model
    def _default_domain_sales_consultant_employee(self):
        """Return only employees with the job position 'Sales Consultant'."""
        return [('job_id.name', '=', 'Sales Consultant')]

    @api.model
    def ir_cron_update_street_address_visibility_project(self):
        """Scheduled action to update street_address_visible"""
        current_time = fields.Datetime.now()
        # Search for records where `street_address_visible` is False
        events = self.search([('street_address_visible', '=', False)])
        for event in events:
            # Check if the record was created more than 3 seconds ago
            if event.create_date and (current_time - event.create_date) >= timedelta(hours=3):
                event.street_address_visible = True
    # sold_design_id = fields.Many2one(
    #     'design',  # Ensure this is the correct model
    #     string='Sold Design',
    #     tracking=True
    # )

    # @api.constrains('phone')
    # def _check_phone(self):
    #     for record in self:
    #         if record.phone:
    #             if not record.phone.isdigit():
    #                 raise ValidationError("Phone must contain only numbers.")
    #             if len(record.phone) != 10:
    #                 raise ValidationError("Phone must be exactly 10 digits.")





    # @api.model
    # def create(self, vals):
    #     # ✅ Block creation for restricted group
    #     if self.env.user.has_group('lytegen_contact_details.group_sales_manager'):
    #         raise AccessError("You do not have the necessary permissions to create this record.")
    #
    #     # ✅ Create the project
    #     project = super(ProjectProject, self).create(vals)
    #
    #     # ✅ Update or create related contact if phone exists
    #     phone = vals.get('phone')
    #     customer_name = vals.get('customer_name')
    #     date_signed = vals.get('date_signed', fields.Date.today())
    #
    #     if phone:
    #         contact = self.env['res.partner'].search([('phone', '=', phone)], limit=1)
    #         if contact:
    #             contact.write({'date_signed': date_signed})
    #         else:
    #             self.env['res.partner'].create({
    #                 'name': customer_name or '',
    #                 'phone': phone,
    #                 'date_signed': date_signed,
    #             })
    #
    #     # ✅ Log project info to Google Sheets
    #     try:
    #         if not phone:
    #             _logger.warning("No phone number provided for project ID: %s", project.id)
    #             return project
    #
    #         # 🔍 Step 1: Find related calendar event
    #         calendar_event = self.env['calendar.event'].sudo().search([('phone_number', '=', phone)], limit=1)
    #         if not calendar_event or not calendar_event.access_token:
    #             _logger.warning("No calendar event or token found for phone: %s", phone)
    #             return project
    #
    #         access_token = calendar_event.access_token
    #         row_index = project._find_row_by_token_in_sheet(access_token)
    #         if row_index is None:
    #             _logger.warning("Access token not found in Google Sheet.")
    #             return project
    #
    #         # 🔍 Step 2: Load and extend the target row
    #         sheet = project._get_google_sheet_4()
    #         existing_row = sheet.row_values(row_index)
    #
    #         def column_letter_to_index(letter):
    #             result = 0
    #             for char in letter.upper():
    #                 result = result * 26 + (ord(char) - ord('A') + 1)
    #             return result - 1
    #
    #         while len(existing_row) <= column_letter_to_index('CK'):
    #             existing_row.append("")
    #
    #         # 🔍 Step 3: Build the row values
    #         row_values = {
    #             # "BO": dict(project._fields['re_roof'].selection).get(project.re_roof, ''),
    #             "BP": dict(project._fields['mount'].selection).get(project.mount, ''),
    #             # "BQ": dict(project._fields['mpu'].selection).get(project.mpu, ''),
    #             "BR": dict(project._fields['hoa'].selection).get(project.hoa, ''),
    #             "BS": dict(project._fields['gated_access'].selection).get(project.gated_access, ''),
    #             "BT": dict(project._fields['battery'].selection).get(project.battery, ''),
    #             "BU": dict(project._fields['utility_bill_holder'].selection).get(project.utility_bill_holder, ''),
    #             # "BV": project.other_utility_bill or '',
    #             "BW": project.provider or '',
    #             "BX": dict(project._fields['finance_type'].selection).get(project.finance_type, ''),
    #             "BY": dict(project._fields['installer'].selection).get(project.installer, ''),
    #             "BZ": dict(project._fields['lead_origin'].selection).get(project.lead_origin, ''),
    #             "CA": dict(project._fields['requested_site_survey_date'].selection).get(
    #                 project.requested_site_survey_date, ''),
    #             "CB": project.custom_ss_times or '',
    #             "CC": ', '.join(project.usage_files.mapped('name')) if project.usage_files else '',
    #             "CD": ', '.join(project.additional_files.mapped('name')) if project.additional_files else '',
    #             "CE": project.notes or '',
    #             "CF": project.special_request or '',
    #             "CG": project.system_size or '',
    #             "CH": project.sold_design_id.design_name or '',
    #             "CI": project.sales_consultant_employee_id.name or '',
    #             "CJ": project.date_start.strftime('%Y-%m-%d') if project.date_start else '',
    #             "CK": project.date.strftime('%Y-%m-%d') if project.date else '',
    #         }
    #
    #         # 🔍 Step 4: Inject values into the row
    #         for col_letter, value in row_values.items():
    #             col_index = column_letter_to_index(col_letter)
    #             existing_row[col_index] = str(value)
    #
    #         # 🔍 Step 5: Update Google Sheet
    #         # sheet.update(f"BO{row_index}:CK{row_index}", [
    #         #     existing_row[column_letter_to_index('BO'):column_letter_to_index('CK') + 1]
    #         # ])
    #         sheet.update(
    #             values=[existing_row[column_letter_to_index('BO'):column_letter_to_index('CK') + 1]],
    #             range_name=f"BO{row_index}:CK{row_index}"
    #         )
    #
    #         _logger.info("Project data logged to Google Sheet at row %s", row_index)
    #
    #     except Exception as e:
    #         _logger.error("Error logging project data to Google Sheets: %s", e)
    #         _logger.error(traceback.format_exc())
    #
    #     return project

    # def write(self, vals):
    #     # Check if the user is in the specified group
    #     if  self.env.user.has_group('lytegen_contact_details.group_sales_manager'):
    #         raise AccessError("You do not have the necessary permissions to modify this record.")
    #
    #     return super(ProjectProject, self).write(vals)
    #
    # @api.onchange(
    #     'hoa', 'gated_access', 'battery', 'utility_bill_holder', 'provider',
    #     'finance_type', 'installer', 'lead_origin', 'requested_site_survey_date',
    #     'custom_ss_times', 'usage_files', 'additional_files', 'notes',
    #     'special_request', 'system_size', 'sold_design_id',
    #     'sales_consultant_employee_id', 'date_start', 'date_end'
    # )
    # def _onchange_log_project_to_google_sheets(self):
    #     """Log Project updates to Google Sheets when key fields are updated."""
    #     for record in self:
    #         if record.create_date and (datetime.now() - record.create_date) > timedelta(minutes=1):
    #             record._log_project_details_to_google_sheets()
    #
    # def _log_project_details_to_google_sheets(self):
    #     """Log project fields to Google Sheets if phone number exists in Column G."""
    #     try:
    #         _logger.info("Logging Project to Google Sheets for Project ID: %s", self.id)
    #
    #         json_keyfile_path = self.env['ir.config_parameter'].sudo().get_param('json_file_path')
    #         if not json_keyfile_path:
    #             _logger.error("Google Sheets JSON keyfile path is missing.")
    #             return False
    #
    #         creds = ServiceAccountCredentials.from_json_keyfile_name(
    #             json_keyfile_path,
    #             ['https://www.googleapis.com/auth/spreadsheets']
    #         )
    #         client = gspread.authorize(creds)
    #
    #         # sheet_id = self.env['ir.config_parameter'].sudo().get_param('google_keys_sheet_id_project')
    #         # worksheet_name = self.env['ir.config_parameter'].sudo().get_param('worksheet_name_project')
    #         sheet_id = "1ySVYemNBmZMoawJ2E_cEQVM0jwjm2rU6Jj48alrPq0U"
    #         worksheet_name = "Sheet1"
    #
    #         if not sheet_id or not worksheet_name:
    #             _logger.error("Google Sheet ID or worksheet name is missing.")
    #             return False
    #
    #         sheet = client.open_by_key(sheet_id)
    #         worksheet = sheet.worksheet(worksheet_name)
    #
    #         phone_number = self.phone
    #         if not phone_number:
    #             _logger.warning("Phone number is missing for Project ID: %s", self.id)
    #             return False
    #
    #         # Phone numbers are stored in Column G (index 7)
    #         PHONE_NUMBER_COLUMN_INDEX = 7
    #         phone_numbers = worksheet.col_values(PHONE_NUMBER_COLUMN_INDEX)
    #
    #         row_values = {
    #             "BO": dict(self._fields['hoa'].selection).get(self.hoa, ''),
    #             "BP": dict(self._fields['gated_access'].selection).get(self.gated_access, ''),
    #             "BQ": dict(self._fields['battery'].selection).get(self.battery, ''),
    #             "BR": dict(self._fields['utility_bill_holder'].selection).get(self.utility_bill_holder, ''),
    #             "BT": self.provider or '',
    #             "BU": dict(self._fields['finance_type'].selection).get(self.finance_type, ''),
    #             "BV": dict(self._fields['installer'].selection).get(self.installer, ''),
    #             "BW": dict(self._fields['lead_origin'].selection).get(self.lead_origin, ''),
    #             "BX": dict(self._fields['requested_site_survey_date'].selection).get(self.requested_site_survey_date,
    #                                                                                  ''),
    #             "BY": self.custom_ss_times or '',
    #             "BZ": ', '.join(self.usage_files.mapped('name')) if self.usage_files else '',
    #             "CA": ', '.join(self.additional_files.mapped('name')) if self.additional_files else '',
    #             "CB": self.notes or '',
    #             "CC": self.special_request or '',
    #             "CD": self.system_size or '',
    #             "CE": self.sold_design_id.name or '',
    #             "CF": self.sales_consultant_employee_id.name or '',
    #             "CG": self.date_start.strftime('%Y-%m-%d') if self.date_start else '',
    #             # "CH": self.date_end.strftime('%Y-%m-%d') if self.date_end else '',
    #         }
    #
    #         if phone_number in phone_numbers:
    #             row_index = phone_numbers.index(phone_number) + 1
    #             for column_letter, value in row_values.items():
    #                 cell_reference = f"{column_letter}{row_index}"
    #                 worksheet.update(range_name=cell_reference, values=[[str(value)]])
    #             _logger.info("Updated existing row for phone number: %s", phone_number)
    #         else:
    #             # Append new row if phone number not found
    #             new_row = [''] * (PHONE_NUMBER_COLUMN_INDEX - 1) + [phone_number]
    #             new_row += list(row_values.values())
    #             worksheet.append_row(new_row)
    #             _logger.info("Added new row for phone number: %s", phone_number)
    #
    #         _logger.info("Successfully logged Project fields to Google Sheets.")
    #         return True
    #
    #     except Exception as e:
    #         _logger.error("Failed to log Project fields to Google Sheets: %s", str(e))
    #         _logger.error(traceback.format_exc())
    #         return False
    #
    # def _find_row_by_token_in_sheet(self, token):
    #     """Search for the row number in the Google Sheet by matching the access token in column B."""
    #     try:
    #         sheet = self._get_google_sheet_4()
    #         if not sheet:
    #             _logger.warning("Google Sheet is not available.")
    #             return None
    #
    #         column_b = sheet.col_values(2)  # Column B = index 2
    #         for idx, value in enumerate(column_b, start=1):
    #             if value.strip() == token.strip():
    #                 _logger.info("Access token matched at row: %s", idx)
    #                 return idx
    #
    #         _logger.warning("Access token '%s' not found in column B", token)
    #         return None
    #
    #     except Exception as e:
    #         _logger.error("Error while searching for access token in sheet: %s", e)
    #         _logger.error(traceback.format_exc())
    #         return None
    #
    # def _get_google_sheet_4(self):
    #     """Returns the worksheet object for CRM Google Sheet."""
    #     try:
    #         _logger.info("Connecting to Google Sheets...")
    #
    #         scope = ['https://www.googleapis.com/auth/spreadsheets']
    #         param = self.env['ir.config_parameter'].sudo()
    #
    #         json_keyfile_path = param.get_param('json_file_path')
    #         if not json_keyfile_path:
    #             _logger.error("Google Sheets JSON keyfile path is missing.")
    #             return None
    #
    #         creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
    #         client = gspread.authorize(creds)
    #
    #         sheet_id = "1ySVYemNBmZMoawJ2E_cEQVM0jwjm2rU6Jj48alrPq0U"
    #         worksheet_name = "Sheet1"
    #
    #         if not sheet_id or not worksheet_name:
    #             _logger.error("Google Sheet ID or worksheet name is missing.")
    #             return None
    #
    #         sheet = client.open_by_key(sheet_id)
    #         worksheet = sheet.worksheet(worksheet_name)
    #
    #         _logger.info("Successfully connected to worksheet: %s", worksheet_name)
    #         return worksheet
    #
    #     except Exception as e:
    #         _logger.error("Failed to access Google Sheet: %s", str(e))
    #         _logger.error(traceback.format_exc())
    #         return None


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    project_ids = fields.Many2many(
        'project.project',
        string="Projects",
        help="Select projects associated with this event"
    )
