# import requests
import pprint
# import json
# from django.conf import settings
# from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
# from rest_framework_simplejwt.serializers import TokenVerifySerializer

# from django.forms import models as model_forms
# from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _

from django.http import HttpResponse

from applications.core.utils import get_tokens
from . import forms

User = get_user_model()


def user_settings_page(request):
    print('******* user_settings_page *******')
    user = {}
    access = ''
    refresh = ''
    access_token = ''
    refresh_token = ''
    user_form = {}
    form_save_result = ''
    user_markers = []

    access, refresh = get_tokens(request)

    if access:
        try:
            access_token_obj = AccessToken(access)
            user = User.objects.get(id=access_token_obj.payload["user_id"])
        except Exception as e:
            print(f'Error get user from access token. Msg: {e}')

    if refresh:
        try:
            refresh_token_obj = RefreshToken(token=refresh)
            print('******* refresh_token_obj: ', refresh_token_obj)
            refresh_token = str(refresh_token_obj)
            access_token = str(refresh_token_obj.access_token)
            if not user:
                access_token_obj = AccessToken(str(refresh_token_obj.access_token))
                user = User.objects.get(id=access_token_obj.payload["user_id"])
        except Exception as e:
            print(f'Error get user from refresh token. Msg: {e}')
            refresh = ''

    if user and not refresh:
        refresh_token_obj = RefreshToken.for_user(user)
        refresh_token = str(refresh_token_obj)
        access_token = str(refresh_token_obj.access_token)

    if request.method == 'POST':
        print(f'******* request.POST:**{request.POST}')
        if user:
            user_form = forms.UserForm(instance=user, data=request.POST)
            if user_form.is_valid():
                user_form.save()
                form_save_result = _('User data saved successfully.')

    if user:
        pprint.pp(user)
        user_form = forms.UserForm(instance=user)
        user_markers = [marker for marker in user.markers.filter(status='published')]
        pprint.pprint(user_markers)
    else:
        user_form = forms.UserForm()

    return render(
        request,
        'account/user_settings_page.html',
        {
            'form_save_result': form_save_result,
            'user': user,
            'user_form': user_form,
            'refresh_token': refresh_token,
            'access_token': access_token,
            'user_markers': user_markers,
        },
    )



# class DashboardView(TemplateView):
#     template_name = 'account/dashboard.html'
#     UserForm = model_forms.modelform_factory(
#         User, fields=[
#             'username',
#             'telegram_id',
#             'telegram_username',
#             'telegram_language',
#             'is_bot',
#         ])

#     def get_initial(self):
#         if self.request.user.is_authenticated:
#             return {
#                 'username': self.request.user.username or '',
#                 'telegram_id': self.request.user.telegram_id or '',
#                 'telegram_username': self.request.user.telegram_username or '',
#                 'telegram_language': self.request.user.telegram_language or '',
#                 'is_bot': self.request.user.is_bot or '',
#             }
#         return {}

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # client_form = self.ClientForm(instance=self.request.user)
#         # client_form.fields['phone'].widget.attrs['data-mask'] = '+0 (000) 000-00-00'
#         context['user_form'] = self.UserForm(instance=self.request.user)
#         # context['refresh_token'] = refresh_token
#         return context

#     def post(self, *args, **kwargs):
#         user_form = self.UserForm(self.request.POST, instance=self.request.user)

#         if user_form.is_valid():
#             user_form.save()

#         return self.render_to_response(self.get_context_data())
