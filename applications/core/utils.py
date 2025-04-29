from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.admin.options import get_content_type_for_model


def logger(
    *,
    obj,
    user,
    message,
    action_flag=ADDITION,
):
    """Записать в LogEntry сообщение по объекту"""
    LogEntry.objects.log_action(
        user_id=user.pk,
        content_type_id=get_content_type_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=message,
    )


def get_tokens(request):
    access = ''
    refresh = ''

    if request.method == 'GET':
        # получаем JWT токены из параметров запроса
        access = request.GET.get('access')
        print(f'******* def get_tokens(request): access:**{access}**')
        refresh = request.GET.get('refresh')
        print(f'******* def get_tokens(request): refresh:**{refresh}**')

    if not access or not refresh:
        if hasattr(request, 'headers') and request.headers:

            # получаем JWT токены из Cookie
            if 'Cookie' in request.headers and request.headers['Cookie']:
                cookie_list = request.headers['Cookie'].split()
                for cookie in cookie_list:
                    print(f'******  cookie: {cookie}')
                    if cookie[-1] == ';':
                        cookie = cookie[:-1]
                    if 'refreshToken=' in cookie:
                        refresh = cookie.split('=')[1]
                        print(f'***** cookie refresh: {refresh}')
                    if 'accessToken=' in cookie:
                        access = cookie.split('=')[1]
                        print(f'***** cookie access: {access}')

            # получаем access токен из Token Bearer Authorization
            if not access and 'Authorization' in request.headers and request.headers['Authorization']:
                authorization_list = request.headers['Authorization'].split()
                if len(authorization_list) == 2:
                    if authorization_list[0] == 'Bearer':
                        access = authorization_list[1]
                        print(f'***** Authorization access: {access}')

    return access, refresh
