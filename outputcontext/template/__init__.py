from django.template.loader import add_to_builtins

def override_include_extend():
    add_to_builtins('outputcontext.template.loader_tags')