def user_perms(request):
    if request.user.is_authenticated:
        return {'user_groups': list(request.user.groups.values_list('name', flat=True)), 'is_admin': request.user.is_superuser}
    return {'user_groups': [], 'is_admin': False}
