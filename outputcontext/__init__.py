__version__ = '1.0.0'
from django.template.loader import add_to_builtins
add_to_builtins('outputcontext.template.loader_tags')