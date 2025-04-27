from django import template

register = template.Library()

@register.filter
def get_item_threshold(thresholds_dict, item_id):
    """Get threshold values for an item from the thresholds dictionary"""
    if item_id in thresholds_dict:
        return thresholds_dict[item_id]
    return {'low': 5, 'medium': 20}  # Default values

@register.filter
def get_low_threshold(threshold_dict):
    """Get the low threshold value"""
    return threshold_dict.get('low', 5)

@register.filter
def get_medium_threshold(threshold_dict):
    """Get the medium threshold value"""
    return threshold_dict.get('medium', 20)