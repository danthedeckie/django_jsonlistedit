import json
from itertools import chain

from django.db import models
from django.core.exceptions import ValidationError
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html, mark_safe

# This Draws the widget into HTML:
class JSONListEditWidget(forms.Widget):

    class Media:
        css = {'all': ('jsonlistedit/jsonlistedit.css',)}
        js = ('jsonlistedit/jsonlistedit.js',)

    def __init__(self, attrs=None, template=None, config={}):
        self.config = config
        if template:
            self.template_name = template
        if not hasattr(self, 'template_name'):
            self.template_name = "jsonlisteditwidget_warning.html"
        return super().__init__(attrs=attrs)
    
    def format_value(self, value):
        return json.dumps(value)

    def value_from_datadict(self, data, files, name):
        raw = data.get(name)
        if raw:
            return json.loads(raw)
        else:
            return None


    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['config'] = self.config #mark_safe(json.dumps(self.config))
        return context


# This tells Django to use the above widget in all forms.
class JSONListEditFormField(forms.Field):
    def __init__(self, **kwargs): #required, label, initial, widget, help_text):
        #kwargs['widget'] = forms.Textarea
        defaults = {}# {'widget': JSONListEditWidget}
        defaults.update(kwargs)
        defaults.pop('max_length')
        defaults['widget'] = JSONListEditWidget(template=defaults.pop('template'), config=defaults.pop('config'))

        return super().__init__(**defaults)

    def clean(self, value):
        return super().clean(value)


# And this stores the data as JSON in the database, and returns it to a python dict / list
class JSONListEditField(models.TextField):
    description = 'A List of things, stored in JSON'

    def __init__(self, *args, template=None, config=None, **kwargs):
        self.config = config
        self.template = template
        super().__init__(*args, **kwargs)

    def parse(self, text):
        try:
            value = json.loads(text)
            return value
        except json.decoder.JSONDecodeError:
            raise ValidationError(_('Invalid JSON'))

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return self.parse(value)

    def to_python(self, value):
        if isinstance(value, list):
            return value
        if value is None:
            return value
        return self.parse(value)

    def value_to_string(self, obj):
        if obj is not None:
            val = getattr(obj, self.attname)
        else:
            val = self.get_default()

        return json.dumps(val)

    def get_prep_value(self, value):
        return json.dumps(value)

    def formfield(self, **kwargs):
        defaults = {'form_class': JSONListEditFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults, template=self.template, config=self.config)
