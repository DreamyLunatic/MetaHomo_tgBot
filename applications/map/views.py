import telegram
from django.contrib.auth import get_user_model
from django.views import generic
from rest_framework import generics, status
from rest_framework.permissions import (AllowAny, BasePermission, IsAuthenticated, IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.serializers import TokenVerifySerializer

from applications.core.utils import get_tokens
from applications.map import models
from applications.map.serializer import (MarkerDeleteSerializer,
                                         MarkerGetSerializer,
                                         MarkerPostSerializer,
                                         MarkerPutSerializer)


User = get_user_model()
bot = telegram.Bot('...')


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = None
        if 'Authorization' in request.headers and request.headers['Authorization']:
            authorization_list = request.headers['Authorization'].split()
            if len(authorization_list) == 2:
                # if authorization_list[0] == 'JWT':
                if authorization_list[0] == 'Bearer':
                    try:
                        access_token = AccessToken(authorization_list[1])
                        user = User.objects.get(id=access_token.payload["user_id"])
                    except Exception as er:
                        print(f'"IsOwner" - Error get user from access_token. Msg: {er}')
        if user:
            return user == obj.user

        return False


# def get_tokens(request):
#     access = ''
#     refresh = ''

#     if request.method == 'GET':
#         # получаем JWT токены из параметров запроса
#         access = request.GET.get('access')
#         print(f'******* def get_tokens(request): access:**{access}**')
#         refresh = request.GET.get('refresh')
#         print(f'******* def get_tokens(request): refresh:**{refresh}**')

#     if not access or not refresh:
#         if hasattr(request, 'headers') and request.headers:
#             print(f'******** request.headers: {request.headers}')

#             # получаем JWT токены из Cookie
#             if 'Cookie' in request.headers and request.headers['Cookie']:
#                 cookie_list = request.headers['Cookie'].split()
#                 for cookie in cookie_list:
#                     print(f'******  cookie: {cookie}')
#                     if cookie[-1] == ';':
#                         cookie = cookie[:-1]
#                     if 'refreshToken=' in cookie:
#                         refresh = cookie.split('=')[1]
#                         # print(f'***** cookie refresh: {refresh}')
#                     if 'accessToken=' in cookie:
#                         access = cookie.split('=')[1]
#                         # print(f'***** cookie access: {access}')

#             # получаем access токен из Token Bearer Authorization
#             if not access and 'Authorization' in request.headers and request.headers['Authorization']:
#                 authorization_list = request.headers['Authorization'].split()
#                 if len(authorization_list) == 2:
#                     if authorization_list[0] == 'Bearer':
#                         access = authorization_list[1]
#                         print(f'***** Authorization access: {access}')

#     return access, refresh


class IndexView(generic.TemplateView):
    template_name = 'map/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = ''
        access = ''
        refresh = ''
        access_token = ''
        refresh_token = ''
        default_latitude_center = '48.72672'
        default_longitude_center = '2.37854'
        default_map_zoom = '8'

        access, refresh = get_tokens(self.request)

        if access:
            try:
                access_token_obj = AccessToken(access)
                user = User.objects.get(id=access_token_obj.payload["user_id"])
            except Exception as e:
                print(f'"IndexView" - Error get user from access token. Msg: {e}')

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
                print(f'"IndexView" - Error get user from refresh token. Msg: {e}')
                refresh = ''

        if user:
            if not refresh:
                refresh_token_obj = RefreshToken.for_user(user)
                refresh_token = str(refresh_token_obj)
                access_token = str(refresh_token_obj.access_token)

            context['latitude_center'] = user.latitude_center or default_latitude_center
            context['longitude_center'] = user.longitude_center or default_longitude_center
            context['map_zoom'] = user.map_zoom or default_map_zoom
            context['refresh_token'] = refresh_token
            context['access_token'] = access_token

        return context


class MarkerList(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = models.Marker.objects.filter(status='published').select_related('user')
    serializer_class = MarkerGetSerializer

    def list(self, request):
        """
        Get all markers
        """

        user = None
        if 'Authorization' in request.headers and request.headers['Authorization']:
            authorization_list = request.headers['Authorization'].split()
            if len(authorization_list) == 2:
                if authorization_list[0] == 'Bearer':
                    try:
                        access_token = AccessToken(authorization_list[1])
                        user = User.objects.get(id=access_token.payload["user_id"])
                    except Exception as e:
                        print(f'"MarkerList" - Error get user from access_token. Msg: {e}')

        queryset = self.get_queryset()
        serializer = MarkerGetSerializer(queryset, many=True)

        for marker in queryset:
            marker.is_owner = True if (user and user == marker.user) else False

        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkerCreate(generics.CreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = models.Marker.objects.all()
    serializer_class = MarkerPostSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        res = self.perform_create(serializer)
        text = f'New marker created: {serializer.data}'
        print(text)
        print('***** MarkerCreate telegram_id: ', self.request.user.telegram_id)
        response_data = serializer.data
        response_data['marker_id'] = serializer.instance.id
        return Response(response_data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MarkerUpdate(generics.UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated&IsOwner]
    queryset = models.Marker.objects.filter(status='published')
    serializer_class = MarkerPutSerializer
    # parser_classes = [MultiPartParser, FormParser]  # TODO нужны ли эти Parser?

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        text = f'Marker updated: {serializer.data}'
        print(text)
        response_data = serializer.data
        response_data['id'] = instance.id
        # return Response(serializer.data)
        # print('******* update request.headers: ', request.headers)
        print('******* update request.user: ', request.user)
        print('******* update request.user.is_authenticated: ', request.user.is_authenticated)
        return Response(response_data)

    def perform_update(self, serializer):
        marker = serializer.instance
        if serializer.validated_data.get('is_delete_photo') == 'true':
            try:
                if marker.photo:
                    marker.photo.delete()
            except Exception as error:
                return Response(
                    f'"MarkerUpdate" - Error when update marker photo. {error}', status=status.HTTP_400_BAD_REQUEST)
        serializer.save()


class MarkerDelete(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated&IsOwner]
    queryset = models.Marker.objects.filter(status='published')
    serializer_class = MarkerDeleteSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        marker_id = instance.id
        telegram_id = instance.user.telegram_id
        telegram_username = instance.user.telegram_username
        text = f'Marker deleted. \nId: {marker_id}, User: {telegram_username}, telegram_id: {telegram_id}'
        print(text)
        self.perform_destroy(instance)
        # async with bot:
        #     await bot.send_message(text=text, chat_id=user_obj.telegram_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()

#########################################################
# import os
# from django.conf import settings
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework.views import APIView



# class IndexView(generic.TemplateView):
#     template_name = 'map/index.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         markers = []
#         markers_obj = models.Marker.objects.filter(status='published')

#         if markers_obj:

#             for m_obj in markers_obj:
#                 marker = {}
#                 marker['id'] = m_obj.id
#                 marker['latitude'] = m_obj.latitude
#                 marker['longitude'] = m_obj.longitude
#                 marker['time'] = str(m_obj.time)
#                 marker['telegram_username'] = ''
#                 if hasattr(m_obj, 'user') and m_obj.user and m_obj.user.telegram_username:
#                     marker['telegram_username'] = m_obj.user.telegram_username
#                 marker['telegram_id'] = ''
#                 if hasattr(m_obj, 'user') and m_obj.user and m_obj.user.username:
#                     marker['telegram_id'] = m_obj.user.username
#                 marker['message'] = m_obj.message
#                 print('m_obj.photo.url: ', m_obj.photo.url if m_obj.photo else '')
#                 marker['photo'] = m_obj.photo.url if m_obj.photo else ''
#                 markers.append(marker)

#             context['markers'] = markers
#         return context


# @csrf_exempt
# async def marker_create_update_view(request):
#     print('******* request dir: ', dir(request))
#     print('******* request user: ', dir(request.auser))
#     print('******* request user: ', request.auser.keywords)
#     print('******* request headers: ', request.headers)
#     print('******* request is_secure: ', request.is_secure())

#     if request.method == 'POST':
#         photo = ''

#         if request.FILES.get('photo'):
#             photo = request.FILES['photo']
#             # print('****** photo: ', photo, photo.name)
#             # photo_name = photo.name

#         data = request.POST.dict()
#         print('data: ', data)
#         request_user = request.POST.get('user')
#         user_obj = await User.objects.filter(username=request_user).afirst()
#         latitude = request.POST.get('latitude')
#         longitude = request.POST.get('longitude')
#         marker_id = request.POST.get('marker_id')
#         message = request.POST.get('message', '').strip()
#         is_delete_photo = request.POST.get('is_delete_photo')

#         if user_obj and latitude and longitude:
#             marker_obj = None

#             if marker_id:
#                 marker_obj = await models.Marker.objects.filter(id=marker_id).afirst()

#             if marker_obj:
#                 marker_obj.latitude = latitude
#                 marker_obj.longitude = longitude

#                 if message:
#                     marker_obj.message = message

#                 if photo and is_delete_photo == 'false':
#                     marker_obj.photo = photo

#                 if is_delete_photo == 'true':
#                     marker_obj.photo = ''

#                 await marker_obj.asave()

#                 async with bot:
#                     text = f'Update marker id: {marker_obj.id} \nUser: {user_obj.telegram_username} \nMessage: {message}\n{photo}'
#                     await bot.send_message(text=text, chat_id=user_obj.telegram_id)

#             else:
#                 marker_obj = await models.Marker.objects.acreate(
#                     user=user_obj,
#                     latitude=latitude,
#                     longitude=longitude,
#                     message=message,
#                     photo=photo,
#                 )

#                 async with bot:
#                     text = f'Create new marker id: {marker_obj.id} \nUser: {user_obj.telegram_username} \nMessage: {message}\n{photo}'
#                     await bot.send_message(text=text, chat_id=user_obj.telegram_id)

#             # print('******* marker_obj id: ', marker_obj.id)

#             return JsonResponse({'status': 'success', 'id': marker_obj.id})
#     return JsonResponse({'status': 'error'})


# @csrf_exempt
# async def marker_delete_view(request, pk):
#     if request.method == "DELETE":
#         marker_obj =  await models.Marker.objects.filter(pk=pk).afirst()

#         if marker_obj:
#             user_obj = await User.objects.filter(id=marker_obj.user_id).afirst()
#             text = f'Delete marker id: {marker_obj.id} \nUser: {user_obj.telegram_username}'
#             delete_result = await marker_obj.adelete()

#             if delete_result[0] == 1:

#                 async with bot:
#                     await bot.send_message(text=text, chat_id=user_obj.telegram_id)

#                 return JsonResponse({'status': 'success', 'id': pk})

#     return JsonResponse({'status': 'error'})


###########################################################



# class MarkerList(generics.ListCreateAPIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#     queryset = models.Marker.objects.filter(status='published').select_related('user')
#     serializer_class = MarkerSerializer

#     def list(self, request):
#         """
#         List all markers
#         """
#         queryset = self.get_queryset()
#         serializer = MarkerSerializer(queryset, many=True)
#         # print(repr(serializer))

#         for marker in queryset:
#             marker.is_owner = True if marker.user == self.request.user else False

#         return Response(serializer.data, status=status.HTTP_200_OK)


# class MarkerCreate(generics.CreateAPIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#     # queryset = models.Marker.objects.filter(status='published').select_related('user')
#     queryset = models.Marker.objects.all()
#     serializer_class = MarkerPostSerializer

#     # def post(self, request, *args, **kwargs):
#     def create(self, request, *args, **kwargs):
#         # print('******* self dir: ', dir(self))
#         # print('******* self request user: ', self.request.user)
#         # print('******* self.kwargs: ', self.kwargs)
#         # authorization = request.headers.get('Authorization', None)
#         # print('***** authorization: ', authorization)
#         # if authorization:
#         #     authorization_list = authorization.split()
#         #     if len(authorization_list) == 2:
#         #         if authorization_list[0] == 'Bearer':
#         #             try:
#         #                 access_token = AccessToken(authorization_list[1])
#         #                 user = User.objects.get(id=access_token.payload["user_id"])
#         #                 print('****** user *** ', user)
#         #             except Exception as er:
#         #                 print(f'Create Pet. Error get user from access_token{er}')

#         # request_data=request.data
#         # request_data['is_owners'] = True if user else False
#         # print('****** request_data: ', request_data)
#         # serializer = self.get_serializer(data=request_data)
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         # serializer.save()
#         return Response(serializer.data)

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)


# class Home(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self, request):

#         # print('******* request dir: ', dir(request))
#         # print('******* request user: ', dir(request.auser))
#         # print('******* request user: ', request.auser.keywords)
#         # print('******* request headers: ', request.headers)
#         # print('******* request is_secure: ', request.is_secure())

#         # print('******* self dir: ', dir(self))
#         # print('******* self request dir: ', dir(self.request))
#         print('******* self request user: ', self.request.user)

#         content = {'message': 'Hello, World!'}
#         return JsonResponse({'status': 'success', 'content': content, 'user': str(self.request.user)})
