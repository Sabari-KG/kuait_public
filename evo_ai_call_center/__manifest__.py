# Copyright © 2024 MaiCall (<https://maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).

{'name': 'EVO AI Call Center',
 'version': '17.0.0.1.06',
 'category': 'Call Center',
 'author': 'MaiCall',
 'website': 'https://maicall.ai',
 'license': 'LGPL-3',
 'summary': """EVO AI Call Center""",
 'depends': ['base', 'mail', 'account'],
 'external_dependencies': {
     'python': ['twilio']
 },
 'data': [
     'data/ir_cron.xml',
     'security/security_groups.xml',
     'security/ir.model.access.csv',
     'views/evo_ai_settings_view.xml',
     'views/evo_call_service_settings_view.xml',
     'views/evo_call_number_view.xml',
     'views/evo_call_campaign_view.xml',
     'views/evo_call_analysis_view.xml',
     'views/evo_call_view.xml',
     'views/evo_call_custom_view.xml',
     'views/res_partner_view.xml',
     'views/evo_data_settings_view.xml',
     'views/evo_call_custom_related_data.xml',
 ],
 'price': 0.0,
 'images': ['static/description/banner.jpg'],
 'currency': 'USD',
 'support': 'support@maicall.ai',
 'installable': True,
 'application': False, }
