from functools import partial
from inspect import getargspec

from django.template.base import parse_bits, StringOrigin, \
    TemplateEncodingError, Parser, Lexer, TagHelperNode, \
    Template as BaseTemplate
from django.template.base import Library as BaseTemplateLibrary
from django.template.context import (Context)

from django.utils.encoding import force_text
from django.utils.itercompat import is_iterable
from django.utils import six
from django.conf import settings



def compile_string(template_string, origin, output_context=None):
    "Compiles template_string into NodeList ready for rendering"
    if settings.TEMPLATE_DEBUG:
        from django.template.debug import DebugLexer, DebugParser

        lexer_class, parser_class = DebugLexer, DebugParser
    else:
        lexer_class, parser_class = Lexer, Parser
    lexer = lexer_class(template_string, origin)
    parser = parser_class(lexer.tokenize())
    parser.output_context = output_context
    return parser.parse()


def generic_tag_compiler(parser, token, params, varargs, varkw, defaults,
                         name, takes_context, output_context, node_class):
    """
    Returns a template.Node subclass.
    """
    bits = token.split_contents()[1:]
    output_context = output_context if output_context is not None else {}
    args, kwargs = parse_bits(parser, bits, params, varargs, varkw,
                              defaults, takes_context, name)
    return node_class(takes_context, output_context, args, kwargs)


class Template(BaseTemplate):
    def __init__(self, template_string, origin=None,
                 name='<Unknown Template>', output_context=None):
        try:
            template_string = force_text(template_string)
        except UnicodeDecodeError:
            raise TemplateEncodingError("Templates can only be constructed "
                                        "from unicode or UTF-8 strings.")
        if settings.TEMPLATE_DEBUG and origin is None:
            origin = StringOrigin(template_string)
        self.nodelist = compile_string(template_string, origin, output_context)
        self.name = name
        self.origin = origin  # for debug toolbar


# The only thing changed compared to django.templates.base.Library.inclusion_tag are the get_template and select_template
class Library(BaseTemplateLibrary):
    def inclusion_tag(self, file_name, context_class=Context,
                      takes_context=False, name=None):
        def dec(func):
            params, varargs, varkw, defaults = getargspec(func)

            class InclusionNode(TagHelperNode):
                def __init__(self, takes_context, output_context, args, kwargs):
                    self.takes_context = takes_context
                    self.args = args
                    self.kwargs = kwargs
                    self.output_context = output_context

                def render(self, context):
                    resolved_args, resolved_kwargs = self.get_resolved_arguments(
                        context)
                    _dict = func(*resolved_args, **resolved_kwargs)

                    if not getattr(self, 'nodelist', False):
                        if isinstance(file_name, Template):
                            t = file_name
                        elif not isinstance(file_name,
                                            six.string_types) and is_iterable(
                                file_name):
                            t = select_template(file_name, self.output_context)
                        else:
                            t = get_template(file_name, self.output_context)
                        self.nodelist = t.nodelist
                    new_context = context_class(_dict, **{
                        'autoescape': context.autoescape,
                        'current_app': context.current_app,
                        'use_l10n': context.use_l10n,
                        'use_tz': context.use_tz,
                    })
                    # Copy across the CSRF token, if present, because
                    # inclusion tags are often used for forms, and we need
                    # instructions for using CSRF protection to be as simple
                    # as possible.
                    csrf_token = context.get('csrf_token', None)
                    if csrf_token is not None:
                        new_context['csrf_token'] = csrf_token
                    return self.nodelist.render(new_context)

            function_name = (name or
                             getattr(func, '_decorated_function',
                                     func).__name__)
            compile_func = partial(generic_tag_compiler,
                                   params=params, varargs=varargs, varkw=varkw,
                                   defaults=defaults, name=function_name,
                                   takes_context=takes_context,
                                   node_class=InclusionNode)
            compile_func.__doc__ = func.__doc__
            self.tag(function_name, compile_func)
            return func

        return dec

from outputcontext.template.loader import get_template, select_template