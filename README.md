## Problem

Django templates have the ability to `extend` and `include` other templates. So a full `HTML` (or other format) output can consist of rendering several templates, which could have been extended or included.

However, each template is rendered separately and is not aware that in the current output there would be other templates involved.

In the case of extended templates the only thing shared is the rendering `context` (*variables, etc*) but still there isn't awareness that other templates are also rendered to make the complete output.

Now, this *"awareness"* sounds like we should sacrifice encapsulation, but there is a solution which in fact improves encapsulation.

Don't think this is aiming *"all templates must share context with variables and other info"*. **It's not about this**. We must, however, enable templates to say *"hey, i need this and this, and i'm rendering that and that, account for me"*. This improves encapsulation.

### Common scenario
You are outputting `HTML`. You have a base template like `layout.html` and other templates like `home.html`. The template `home.html` also includes `_nav.html` and `_footer.html`. 

Now, `_footer.html` and `_nav.html` have some cool animations going on. So they need certain `CSS` and `JavaScript` files. Right now in Django, you can't define these in the `_footer.html` and `_nav.html` because included templates neither share context, nor can influence `block` tags.

So you end up defining the required `CSS` and `JavaScript` for the partials in either `home.html` or `layout.html`. This way you already make `home.html` and `layout.html` aware of the partials and if partials change, `home.html` and `layout.html` should also change. That is not good encapuslation.

## Solution
Django templates are rendered on 2 levels:

 - **parser level rendering** (compile template to DOM-like structure)
 - **context level rendering** (with context and variables)

We aim better encapsulation so let limit ourselves to **parser level**. This is the lower level rendering where we only see template nodes and no variables - something like DOM.

Django developers had taken the similar approach to attach `__loaded_blocks` attribute to the parser object when dealing with `block` tag.

### What `django-output-context` does?
`django-output-context` adds a **parser-level** context that is shared with all templates involved in making the complete output (extended and included).

The context is attached to the template `parser` which is passed to django tags registed via `@register.tag('yourtag')` so you can now write your own tags that make use of this context to communicate template requirements or planned structure.

### How it does this?
It overrides `include` and `extend` template tags. There's a lot of code duplicated from django codebase, and that's because **the only thing** that `django-output-context` do is to add a `output_context`  parameter to all calls that start from `include` and `extend` tags down to the `compile_string` function that creates the parser.

With this goes and [a ticket](https://code.djangoproject.com/ticket/23591#ticket) so that Django can possible make this a core feature.

## Installation

Replace `'django.template.loaders.app_directories.Loader'` entry from `TEMPLATE_LOADERS` (defined in `settings.py`) with `outputcontext.template.loaders.app_directories.Loader`
tories.Loader`.

So it will look something like this:

```
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'outputcontext.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)
```