from django.template.base import TemplateSyntaxError, Variable, token_kwargs
from django.template.loader_tags import BlockNode, BaseIncludeNode, ExtendsNode as BaseExtendNode
from django.conf import settings

from outputcontext.template.base import Library
from outputcontext.template.loader import get_template

register = Library()

class ConstantIncludeNode(BaseIncludeNode):
    def __init__(self, template_path, output_context, *args, **kwargs):
        super(ConstantIncludeNode, self).__init__(*args, **kwargs)
        try:
            t = get_template(template_path, output_context)
            self.template = t
        except:
            if settings.TEMPLATE_DEBUG:
                raise
            self.template = None

    def render(self, context):
        if not self.template:
            return ''
        return self.render_template(self.template, context)

class IncludeNode(BaseIncludeNode):
    def __init__(self, template_name, output_context, *args, **kwargs):
        super(IncludeNode, self).__init__(*args, **kwargs)
        self.template_name = template_name
        self.output_context = output_context

    def render(self, context):
        try:
            template_name = self.template_name.resolve(context)
            template = get_template(template_name, self.output_context)
            return self.render_template(template, context)
        except:
            if settings.TEMPLATE_DEBUG:
                raise
            return ''


class ExtendsNode(BaseExtendNode):

    def __init__(self, nodelist, parent_name, template_dirs=None, output_context=None):
        self.nodelist = nodelist
        self.parent_name = parent_name
        self.template_dirs = template_dirs
        self.blocks = dict([(n.name, n) for n in nodelist.get_nodes_by_type(BlockNode)])
        self.output_context = output_context

    def get_parent(self, context):
        parent = self.parent_name.resolve(context)
        if not parent:
            error_msg = "Invalid template name in 'extends' tag: %r." % parent
            if self.parent_name.filters or\
                    isinstance(self.parent_name.var, Variable):
                error_msg += " Got this from the '%s' variable." %\
                    self.parent_name.token
            raise TemplateSyntaxError(error_msg)
        if hasattr(parent, 'render'):
            return parent # parent is a Template object
        return get_template(parent, self.output_context)



# The only thing changed compared to django.templates.loader_tags.do_include are the Node Classes
@register.tag('include')
def do_include(parser, token):
    # start same as django code @ django.templates.loader_tags.do_include
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("%r tag takes at least one argument: the name of the template to be included." % bits[0])
    options = {}
    remaining_bits = bits[2:]
    while remaining_bits:
        option = remaining_bits.pop(0)
        if option in options:
            raise TemplateSyntaxError('The %r option was specified more '
                                      'than once.' % option)
        if option == 'with':
            value = token_kwargs(remaining_bits, parser, support_legacy=False)
            if not value:
                raise TemplateSyntaxError('"with" in %r tag needs at least '
                                          'one keyword argument.' % bits[0])
        elif option == 'only':
            value = True
        else:
            raise TemplateSyntaxError('Unknown argument for %r tag: %r.' %
                                      (bits[0], option))
        options[option] = value
    isolated_context = options.get('only', False)
    namemap = options.get('with', {})
    path = bits[1]
    if not hasattr(parser, 'output_context') or parser.output_context is None:
        parser.output_context = {}
    if path[0] in ('"', "'") and path[-1] == path[0]:
        return ConstantIncludeNode(path[1:-1], extra_context=namemap,
                                   isolated_context=isolated_context, output_context=parser.output_context)
    return IncludeNode(parser.compile_filter(bits[1]), extra_context=namemap,
                       isolated_context=isolated_context, output_context=parser.output_context)




@register.tag('extends')
def do_extends(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument" % bits[0])
    parent_name = parser.compile_filter(bits[1])
    nodelist = parser.parse()
    if nodelist.get_nodes_by_type(ExtendsNode):
        raise TemplateSyntaxError("'%s' cannot appear more than once in the same template" % bits[0])

    if not hasattr(parser, 'output_context') or parser.output_context is None:
        parser.output_context = {}
    return ExtendsNode(nodelist, parent_name, None, parser.output_context)
