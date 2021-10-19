# Generated by Django 3.2.5 on 2021-09-22 18:20

from django.db import migrations

from tdpservice.users.permissions import (
    create_perms,
    get_permission_ids_for_model,
    view_permissions_q
)


def set_owasp_zap_scan_permissions(apps, schema_editor):
    """Set permissions for the OwaspZapScan model for relevant groups."""
    ofa_admin = apps.get_model('auth', 'Group').objects.get(name='OFA Admin')
    ofa_system_admin = (
        apps.get_model('auth', 'Group')
            .objects
            .get(name='OFA System Admin')
    )

    zap_scan_permissions = get_permission_ids_for_model(
        'security',
        'owaspzapscan',
        filters=[view_permissions_q]
    )

    # Only OFA Admin and OFA System Admin need access to this model
    ofa_admin.permissions.add(*zap_scan_permissions)
    ofa_system_admin.permissions.add(*zap_scan_permissions)

    # On new systems the previous migration for OFA System Admin will add extra
    # permissions, remove these if so.
    unwanted_permissions = get_permission_ids_for_model(
        'security',
        'owaspzapscan',
        exclusions=[view_permissions_q]
    )

    ofa_system_admin.permissions.remove(*unwanted_permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_add_clam_av_file_scan_perms'),
    ]

    operations = [
        # We need to call this again to ensure permissions are created for
        # the newly added OwaspZapScan model.
        migrations.RunPython(
            create_perms,
            reverse_code=migrations.RunPython.noop
        ),
        migrations.RunPython(
            set_owasp_zap_scan_permissions,
            reverse_code=migrations.RunPython.noop
        )
    ]