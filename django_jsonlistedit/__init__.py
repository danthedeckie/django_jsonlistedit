import json
from itertools import chain

from django.db import models
from django.core.exceptions import ValidationError
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html, mark_safe

def make_textarea_tmpl(name, attrs, value):
    """
        Given the (name, attributes, value) tuple that a Widget.render is given,
        return a list of "{}" type format strings which can be ''.join-ed together,
        and a list of values to populate it, to produce a full <textarea> HTML input.
        This will eventually get handed to the 'format_html' django util.
    """
    attrs['autocomplete'] = 'false'
    if not 'debug' in attrs:
        attrs['debug'] = False

    formatstr = ['<textarea name="{}" ']
    values = [name]
    #l += list(chain(*attrs.items()))
    for k, v in attrs.items():
        values.append(k)
        if v == True:
            formatstr.append('{} ')
        else:
            values.append(v)
            formatstr.append('{}="{}" ')

    formatstr.append('>{}</textarea>')
    values.append(json.dumps(value) if value is not None else '')

    return formatstr, values

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

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['config'] = self.config #mark_safe(json.dumps(self.config))
        return context

    def render2(self, name, value, attrs=None, renderer=None):
        # Rather than use a separate django or jinja template, this just does it here.
        # Probably a bad idea.  But seems to work for something this simple for now...

        formatstr, vals = make_textarea_tmpl(name, attrs, value)

        if 'beforeHTML' in self.config:
            formatstr.insert(0, self.config['beforeHTML'])

        script = '''
        <script>new JSONListEdit(document.getElementById('{}'), {});</script>
        '''

        vals.append(attrs['id'])
        vals.append(mark_safe(json.dumps(self.config)))

        if 'afterHTML' in self.config:
            formatstr.append(self.config['afterHTML'])

        return format_html(''.join(formatstr) + script, *vals)


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

    def get_prep_value(self, value):
        return json.dumps(value)

    def formfield(self, **kwargs):
        defaults = {'form_class': JSONListEditFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults, template=self.template, config=self.config)