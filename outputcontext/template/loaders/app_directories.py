from django.template.loaders.app_directories import \
    Loader as AppDirectoriesLoader
from django.template.loader import make_origin, TemplateDoesNotExist, add_to_builtins

from outputcontext.template.loader import get_template_from_string

class Loader(AppDirectoriesLoader):

    def __call__(self, template_name, template_dirs=None, output_context=None):
        return self.load_template(template_name, template_dirs, output_context)

    def load_template(self, template_name, template_dirs=None,
                      output_context=None):
        source, display_name = self.load_template_source(template_name,
                                                         template_dirs)
        origin = make_origin(display_name, self.load_template_source,
                             template_name, template_dirs)
        try:
            template = get_template_from_string(source, origin, template_name,
                                                output_context)
            return template, None
        except TemplateDoesNotExist:
            # If compiling the template we found raises TemplateDoesNotExist, back off to
            # returning the source and display name for the template we were asked to load.
            # This allows for correct identification (later) of the actual template that does
            # not exist.
            return source, display_name

add_to_builtins('outputcontext.template.loader_tags')