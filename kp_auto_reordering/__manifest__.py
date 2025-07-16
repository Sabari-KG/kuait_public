# -- coding: utf-8 --
{
    "name": "KP Auto Re-ordering",
    "summary": "Auto Re-Ordering Custom",
    "version": "1.2.1",
    "author": "KPGTC",
    "website": "https://kuwaitprotocol.com",
    "support": "https://support.kuwaitprotocol.com",
    "maintainer": "KPGTC",
    "depends": ['stock','mail'],
    "data": [
        # 'data/auto_reorder_crom.xml',
        'data/reorder_config_cron.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/stock_orderpoint.xml',
        'views/reorder_update_config_views.xml',
        'views/reorder_history.xml'
    ],
    "license": "OPL-1",
}
