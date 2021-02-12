from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    rename_fields_remove_suffix(env)


@openupgrade.logging()
def rename_fields_remove_suffix(env):
    """Rename fields that have ``_id`` suffix, but they're  actually type char"""
    if not openupgrade.column_exists(env.cr, 'crm_lead', 'facebook_form_id'):
        return
    columns_to_rename = {
        'crm_lead': [('facebook_form_id', 'id_facebook_form')],
        'crm_facebook_form': [('facebook_form_id', 'id_facebook_form')],
        'utm_adset': [('facebook_adset_id', 'id_facebook_adset')],
        'utm_campaign': [('facebook_campaign_id', 'id_facebook_campaign')],
        'utm_medium': [('facebook_ad_id', 'id_facebook_ad')],
    }
    openupgrade.rename_columns(env.cr, columns_to_rename)
