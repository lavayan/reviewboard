import logging
from urllib import quote as urllib_quote

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from djblets.util.http import set_last_modified
from djblets.webapi.errors import DOES_NOT_EXIST

from reviewboard.diffviewer.diffutils import get_original_file
from reviewboard.webapi.base import WebAPIResource
from reviewboard.webapi.decorators import webapi_check_login_required
from reviewboard.webapi.errors import FILE_RETRIEVAL_ERROR
from reviewboard.webapi.resources import resources


class OriginalFileResource(WebAPIResource):
    """Provides the unpatched file corresponding to a file diff."""
    name = 'original_file'
    singleton = True
    allowed_item_mimetypes = ['text/plain']

    @webapi_check_login_required
    def get(self, request, *args, **kwargs):
        """Returns the original unpatched file.

        The file is returned as :mimetype:`text/plain` and is the original
        file before applying a patch.
        """
        try:
            filediff = resources.filediff.get_object(request, *args, **kwargs)
        except ObjectDoesNotExist:
            return DOES_NOT_EXIST

        if filediff.is_new:
            return DOES_NOT_EXIST

        try:
            orig_file = get_original_file(filediff, request=request)
        except Exception, e:
            logging.error("Error retrieving original file: %s", e, exc_info=1,
                          request=request)
            return FILE_RETRIEVAL_ERROR

        resp = HttpResponse(orig_file, mimetype='text/plain')
        filename = urllib_quote(filediff.source_file)
        resp['Content-Disposition'] = 'inline; filename=%s' % filename
        set_last_modified(resp, filediff.diffset.timestamp)

        return resp


original_file_resource = OriginalFileResource()
