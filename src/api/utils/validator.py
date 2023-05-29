import json
import re
import io
from PIL import Image
from ..errors import srm_errors

UUID_REGEX = '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
FILE_NAME_REGEX = '^[A-Za-z0-9_.-]+\.(jpg|jpeg|png)$'


class ImageUploadValidator:
    @staticmethod
    def validate(request_id, pagination: json, file_name, image_file):
        if not (re.match(UUID_REGEX, request_id)):
            raise srm_errors.InvalidRequestIdError(request_id)

        if not re.match(FILE_NAME_REGEX, file_name):
            raise srm_errors.InvalidFileNameError(file_name)

        try:
            total = int(pagination.get("total"))
        except ValueError:
            raise srm_errors.InvalidNumberError(total)

        try:
            page = int(pagination.get("page"))
        except ValueError:
            raise srm_errors.InvalidNumberError(page)

        try:
            Image.open(io.BytesIO(image_file))
        except IOError:
            raise srm_errors.InvalidFileError(file_name)
