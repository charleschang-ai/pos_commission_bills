# -*- coding: utf-8 -*-
################################################################################
#    Author: Don Shan
#
################################################################################
{
    'name': 'Point Of Sale Commission And Bills',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """POS-based efficient commission sales.""",
    'description': """POS Commission And Bills is a powerful enhancement for Odoo Point of Sale that helps 
    businesses automate commission tracking, streamline billing, and improve financial transparency. 
    Whether you manage retail stores, restaurants, or service-based POS operations, 
    this module ensures accurate commission calculation and effortless settlement with staff or partners.""",
    'author': 'Don Shan',
    'maintainer': 'Don Shan',
    'depends': ['base', 'point_of_sale', 'pos_loyalty'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/commission_calculation.xml',
        'views/product_template.xml',
        'views/pos_order_view.xml',
        'views/pos_order_line_view.xml',
        'views/account_move_view.xml',
        'views/pos_details.xml',
        'views/pos_session_sales_details.xml'
    ],
    "assets": {
        'web.assets_backend': [
            'pos_commission_bills/static/src/js/**/*',
            'pos_commission_bills/static/src/xml/**/*',
        ],
        'point_of_sale._assets_pos': [
            'pos_commission_bills/static/src/pos/**/*',
        ],
    },
    'images': ['static/description/icon.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 45,
    'currency': "USD",
}
