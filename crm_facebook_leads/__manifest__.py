{
    'name': "CRM Facebook Lead Ads",
    'summary': """
        Sync Facebook Leads with Odoo CRM""",
    'author': "BADEP, Vauxoo",
    'website': "https://badep.ma, www.vauxoo.com",
    'category': 'Sales/CRM',
    'version': "16.0.1.0.0",
    'depends': [
        'crm',
    ],
    'license': 'AGPL-3',
    'data': [
        'data/ir_config_parameter_data.xml',
        'data/ir_cron_data.xml',
        'security/ir.model.access.csv',
        'views/crm_facebook_form_views.xml',
        'views/crm_facebook_page_views.xml',
        'views/crm_lead_views.xml',
    ],
    'application': True,
}
