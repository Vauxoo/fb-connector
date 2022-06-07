from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    rename_field_odoo_field(env)


@openupgrade.logging()
def rename_field_odoo_field(env):
    """Rename field ``odoo_field`` on model ``crm.facebook.form.field`` to add missing _id suffix"""
    openupgrade.rename_fields(
        env,
        field_spec=[
            ("crm.facebook.form.field", "crm_facebook_form_field", "odoo_field", "odoo_field_id"),
        ]
    )
