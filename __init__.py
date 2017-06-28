import json
from itertools import chain

from django.db import models
from django.core.exceptions import ValidationError
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html, mark_safe

class JSONListEditWidget(forms.Widget):
    class Media:
        css = {'all': ('jsonlistedit/jsonlistedit.css',)}
        js = ('jsonlistedit/jsonlistedit.js',)

    def render(self, name, attrs, value):
        attrs['autocomplete'] = 'false'
        if not 'debug' in attrs:
            attrs['debug'] = False

        f = ['<textarea name="{}" ']
        l = [name]
        #l += list(chain(*attrs.items()))
        for k,v in attrs.items():
            l.append(k)
            if v == True:
                f.append('{} ')
            else:
                l.append(v)
                f.append('{}="{}" ')

        f.append('>{}</textarea>')
        i = len(l)
        l.append(json.dumps(value) if value is not None else '')

        script = '''
        <script>new JSONListEdit(document.getElementById('{}'),
            {{debug: {},
            templates: {},
            }});</script>
        '''

        l.append(attrs['id'])
        l.append('true' if attrs['debug'] else 'false')

        templates = mark_safe('''{
            'default': '= $$name'
}''')
        l.append(templates)

        return format_html(''.join(f) + script, *l)

class JSONListEditFormField(forms.Field):
    def __init__(self, **kwargs): #required, label, initial, widget, help_text):
        #kwargs['widget'] = forms.Textarea
        defaults = {}# {'widget': JSONListEditWidget}
        kwargs.pop('max_length') # TODO: WHY???!?!?!
        defaults.update(kwargs)
        defaults['widget'] = JSONListEditWidget
        return super().__init__(**defaults)

    def clean(self, value):
        return super().clean(value)

class JSONListEditField(models.TextField):
    description = 'A List of things, stored in JSON'

    def __init__(self, *args, **kwargs):
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

    def get_prep_value(self, value):
        return json.dumps(value)

    def formfield(self, **kwargs):
        defaults = {'form_class': JSONListEditFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)