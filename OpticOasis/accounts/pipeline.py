def get_additional_fields(strategy, details, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    fields = {
        'first_name': details.get('first_name', ''),
        'last_name': details.get('last_name', ''),
        'phone_number': '',  # Collect this from the user if necessary
    }
    return {'is_new': True, 'fields': fields}

def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    fields = kwargs.get('fields', {})
    return {
        'is_new': True,
        'user': strategy.create_user(
            email=details['email'],
            first_name=fields['first_name'],
            last_name=fields['last_name'],
            phone_number=fields['phone_number'],
        )
    }