from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guestbook', '0003_guestbookentry_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='bg_image',
            field=models.ImageField(
                blank=True,
                help_text='Background image shown on the downloadable signing board',
                null=True,
                upload_to='events/bg',
                verbose_name='Download Canvas Background',
            ),
        ),
    ]