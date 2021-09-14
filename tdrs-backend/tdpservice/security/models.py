from hashlib import sha256
import logging

from django.contrib.admin.models import ContentType, LogEntry, ADDITION
from django.core.files.base import File
from django.db import models

from tdpservice.data_files.models import DataFile
from tdpservice.users.models import User

logger = logging.getLogger(__name__)


class ClamAVFileScanManager(models.Manager):
    """Extends object manager functionality with common operations."""

    def record_scan(
        self,
        file: File,
        msg: str,
        result: 'ClamAVFileScan.Result',
        uploaded_by: User
    ) -> 'ClamAVFileScan':
        """Create a new ClamAVFileScan instance with associated LogEntry."""
        try:
            file_shasum = sha256(file.read()).hexdigest()
        except (TypeError, ValueError) as err:
            logger.error(f'Encountered error deriving file hash: {err}')
            file_shasum = 'INVALID'

        av_scan = self.model.objects.create(
            file_name=file.name,
            file_size=file.size,
            file_shasum=file_shasum,
            result=result,
            uploaded_by=uploaded_by
        )

        # Create a new LogEntry that is tied to this model instance.
        content_type = ContentType.objects.get_for_model(ClamAVFileScan)
        LogEntry.objects.log_action(
            user_id=uploaded_by.pk,
            content_type_id=content_type.pk,
            object_id=av_scan.pk,
            object_repr=str(av_scan),
            action_flag=ADDITION,
            change_message=msg
        )

        return av_scan


class ClamAVFileScan(models.Model):
    """Represents a ClamAV virus scan performed for an uploaded file."""

    class Meta:
        verbose_name = 'Clam AV File Scan'

    class Result(models.TextChoices):
        """Represents the possible results from a completed ClamAV scan."""
        CLEAN = 'CLEAN'
        INFECTED = 'INFECTED'
        ERROR = 'ERROR'

    scanned_at = models.DateTimeField(auto_now_add=True)
    file_name = models.TextField()
    file_size = models.PositiveBigIntegerField(
        help_text='The file size in bytes'
    )
    file_shasum = models.TextField(
        help_text='The SHA256 checksum of the uploaded file'
    )
    result = models.CharField(
        choices=Result.choices,
        help_text='Scan result for uploaded file',
        max_length=12
    )
    uploaded_by = models.ForeignKey(
        User,
        help_text='The user that uploaded the scanned file',
        null=True,
        on_delete=models.SET_NULL,
        related_name='av_scans'
    )

    data_file = models.ForeignKey(
        DataFile,
        blank=True,
        help_text='The resulting DataFile object if this scan was clean',
        null=True,
        on_delete=models.SET_NULL,
        related_name='av_scans'
    )

    objects = ClamAVFileScanManager()

    def __str__(self) -> str:
        """Return string representation of model instance."""
        return f'{self.file_name} ({self.file_size_humanized}) - {self.result}'

    @property
    def file_size_humanized(self) -> str:
        """Convert the file size into the largest human readable unit."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                break
            size /= 1024.0

        return f'{size:.{2}f}{unit}'
