from django import template

register = template.Library()


@register.filter
def attr(obj, name):
    return getattr(obj, name, "")


@register.filter
def get_item(mapping, key):
    return mapping.get(key)
