# -*- coding: utf-8 -*-
{
        'name'                 : "Psychological Tests",

        'summary'              : "Short (1 phrase/line) summary of the module's purpose",

        'description'          : """
Long description of module's purpose
    """,

        'author'               : "Mahmoud Abd Al-Razek Hussein - Email: [mabdalrazek994@gmail.com] - phone: +0201112118819",
        'website'              : "https://www.yourcompany.com",

        # Categories can be used to filter modules in modules listing
        # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
        # for the full list
        'category'             : 'Uncategorized',
        'version'              : '17.0.0.0.6',
        # 'license'    : 'AGPL-3',
        'license'              : 'LGPL-3',

        # any module necessary for this one to work correctly
        # 'web_enterprise'
        'depends'              : ['base', 'web', 'website', 'web_enterprise'],

        # always loaded
        'data'                 : [
                # 'security/psychological_tests_security.xml',
                'security/ir.model.access.csv',

                'views/personality_test_views.xml',
                'views/test_type.xml',
                'views/test_type_question.xml',
                'views/test_type_option.xml',
                'views/test_type_answer.xml',
                'views/test_type_statistics.xml',

                # templates for website
                'views/website_menu.xml',
                'views/website_templates.xml',
                'views/website_start_and_result_template.xml',
                'views/test_result_line_views.xml',

                'views/res_config_settings_view.xml',

                'views/base_menu.xml',

        ],

        'external_dependencies': {
                'python': ['fuzzywuzzy', 'python-Levenshtein'],
        },

        'assets'               : {
                'web.assets_frontend'      : [
                        # 'psychological_tests/static/src/css/font.css',
                        # 'psychological_tests/static/src/css/style.css',
                        'psychological_tests/static/src/js/test_navigation.js',

                ],

                'web.assets_backend'       : [
                        #                         'psychological_tests/static/src/css/font.css',
                        # 'psychological_tests/static/src/css/style.css',
                        'psychological_tests/static/src/js/test_navigation.js',

                ],

                'web.reports_assets_common': [
                        # 'psychological_tests/static/src/css/font.css',
                        #                         'psychological_tests/static/src/css/style.css',
                ],

                'web.assets_qweb'          : [

                ],
        },

        'installable'          : True,
        'application'          : True,

        # only loaded in demonstration mode

}
