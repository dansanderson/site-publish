import logging
from google.appengine.ext import endpoints
from protorpc import messages
from protorpc import remote

import models
import publish

CLIENT_IDS = ['145889693104-t0nm6og9vt8qmrdkus1aecm7d45stcgr.'
              'apps.googleusercontent.com',
              endpoints.API_EXPLORER_CLIENT_ID]
CONTENT_DEVELOPERS = ['dan.sanderson@gmail.com']


class GenericResponse(messages.Message):
    pass


class StartRequest(messages.Message):
    project_prefixes = messages.StringField(1, repeated=True)
    upload_paths = messages.StringField(2, repeated=True)


class StartResponse(messages.Message):
    change_id = messages.IntegerField(1, required=True)


class UploadRequest(messages.Message):
    change_id = messages.IntegerField(1, required=True)
    url_path = messages.StringField(2, required=True)
    content_type = messages.StringField(3, required=True)
    data = messages.BytesField(4, required=True)


class CommitRequest(messages.Message):
    change_id = messages.IntegerField(1, required=True)


def ValidateUserIsAuthorized():
    """Raises endpoints.UnauthorizedException if the caller is not signed in
    or is not allowed to publish content.
    """
    user = endpoints.get_current_user()
    if user is None or user.email() not in CONTENT_DEVELOPERS:
        raise endpoints.UnauthorizedException()


@endpoints.api(
    name='sitepublish',
    version='v1',
    description='Site Publish API',
    allowed_client_ids=CLIENT_IDS)
class SitePublishApi(remote.Service):

    @endpoints.method(
        StartRequest,
        StartResponse,
        name='start', path='start')
    def start(self, request):
        ValidateUserIsAuthorized()
        change = publish.start_change(
            request.project_prefixes,
            request.upload_paths,
            endpoints.get_current_user())
        response = StartResponse(change_id=change.get_change_id())
        return response

    @endpoints.method(
        UploadRequest,
        GenericResponse,
        name='upload', path='upload')
    def upload(self, request):
        ValidateUserIsAuthorized()
        change_key = models.Change.get_key(request.change_id)
        change = change_key.get()
        if change is None:
            raise endpoints.BadRequestException(
                'Invalid change ID.')
        if request.url_path not in change.upload_paths:
            raise endpoints.BadRequestException(
                'Unexpected upload for path %s.' % request.url_path)
        if len(request.data) > 900 * 1024:
            raise endpoints.BadRequestException(
                'Uploaded data cannot exceed 900 kilobytes.')

        publish.create_content(
            request.change_id,
            request.url_path,
            request.content_type,
            request.data)

        return GenericResponse()

    @endpoints.method(
        CommitRequest,
        GenericResponse,
        name='commit', path='commit')
    def commit(self, request):
        ValidateUserIsAuthorized()
        publish.commit_change(request.change_id)
        return GenericResponse()


app = endpoints.api_server([SitePublishApi], restricted=False)
