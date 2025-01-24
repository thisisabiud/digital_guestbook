from django import template
import random

register = template.Library()

@register.filter
def random_rotation(value):
    return random.randint(-15, 15)

@register.filter
def random_top(value):
    return random.randint(0, 600)

@register.filter
def random_left(value):
    return random.randint(0, 100)