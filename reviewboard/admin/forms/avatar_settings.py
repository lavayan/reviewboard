"""Administration form for avatar settings."""

from __future__ import unicode_literals

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from djblets.siteconfig.forms import SiteSettingsForm

from reviewboard.avatars import avatar_services


class AvatarServicesForm(SiteSettingsForm):
    """A form for managing avatar services."""

    avatars_enabled = forms.BooleanField(
        label=_('Enable avatars'),
        required=False)

    enabled_services = forms.MultipleChoiceField(
        label='Enabled avatar services',
        help_text=_('The avatar services which are available to be used.'),
        required=False,
        widget=FilteredSelectMultiple(_('Avatar Services'), False))

    default_service = forms.ChoiceField(
        label=_('Default avatar service'),
        help_text=_('The avatar service to be used by default for users who '
                    'do not have an avatar service configured. This must be '
                    'one of the enabled avatar services below.'),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(AvatarServicesForm, self).__init__(*args, **kwargs)
        default_choices = [('none', 'None')]
        enable_choices = []

        for service in avatar_services:
            default_choices.append((service.avatar_service_id, service.name))
            enable_choices.append((service.avatar_service_id, service.name))

        self.fields['default_service'].choices = default_choices
        self.fields['enabled_services'].choices = enable_choices
        self.fields['enabled_services'].initial = [
            service.avatar_service_id
            for service in avatar_services.enabled_services
        ]

        default_service = avatar_services.default_service

        if avatar_services.default_service is not None:
            self.fields['default_service'].initial = \
                default_service.avatar_service_id

    def clean_enabled_services(self):
        """Clean the enabled_services field.

        Raises:
            django.core.exceptions.ValidationError:
                Raised if an unknown service is attempted to be enabled.
        """
        for service_id in self.cleaned_data['enabled_services']:
            if not avatar_services.has_service(service_id):
                raise ValidationError('Unknown service "%s"' % service_id)

        return self.cleaned_data['enabled_services']

    def clean(self):
        """Clean the form.

        This will clean the form, handling any fields that need cleaned
        that depend on the cleaned data of other fields.

        Raises:
            django.core.exceptions.ValidationError:
                Raised if an unknown service or disabled service is set to be
                the default.
        """
        cleaned_data = super(AvatarServicesForm, self).clean()

        enabled_services = set(cleaned_data['enabled_services'])
        service_id = cleaned_data['default_service']

        if service_id == 'none':
            default_service = None
        else:
            if not avatar_services.has_service(service_id):
                raise ValidationError('Unknown service "%s".' % service_id)
            elif service_id not in enabled_services:
                raise ValidationError('Cannot set disabled service "%s" to '
                                      'default.'
                                      % service_id)

            default_service = avatar_services.get('avatar_service_id',
                                                  service_id)

        cleaned_data['default_service'] = default_service

        return cleaned_data

    def save(self):
        """Save the enabled services and default service to the database."""
        avatar_services.set_enabled_services(
            [
                avatar_services.get('avatar_service_id', service_id)
                for service_id in self.cleaned_data['enabled_services']
            ],
            save=False)

        avatar_services.set_default_service(
            self.cleaned_data['default_service'],
            save=False)

        avatar_services.avatars_enabled = self.cleaned_data['avatars_enabled']
        avatar_services.save()

    class Meta:
        title = _('Avatar Services')
        fieldsets = (
            {
                'fields': ('avatars_enabled', 'default_service',
                           'enabled_services'),
            },
        )
