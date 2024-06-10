def extract_language(description):
    description_lower = description.lower()
    if 'javascript' in description_lower:
        return 'javascript'
    elif 'ruby' in description_lower:
        return 'ruby'
    else:
        return 'python'  # Default language