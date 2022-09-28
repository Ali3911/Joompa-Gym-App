def response_json(status, data, message=None, optional_data=None):
    return {"data": data, "status": status, "message": message, "optional_data": optional_data}


def user_profile_data_exists(attribute_name, fk, model_name):
    """Public Method

    The method checks if the user profile data for the given model value exist or not.

    Parameters
    ----------
    attribute_name : django.db
    fk : integer
    model_name : django.db

    Returns
    -------
    boolean
        returns true if data exists, returns false otherwise
    """

    kwargs = {"{0}".format(attribute_name): fk}

    if attribute_name == "baseline_assessment":
        user_object = model_name.objects.filter(baseline_assessment__contains=[{"id": fk}])

    else:
        user_object = model_name.objects.filter(**kwargs)

    if user_object.count() > 0:
        return True

    return False
