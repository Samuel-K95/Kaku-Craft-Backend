from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitecontent",
            name="section",
            field=models.CharField(
                choices=[
                    ("home_hero", "Home Hero"),
                    ("home_about_teaser", "Home About Teaser"),
                    ("about", "About"),
                    ("contact", "Contact"),
                    ("banner", "Promotional Banner"),
                    ("special_occasion", "Special Occasion"),
                    ("new_arrivals", "New Arrivals"),
                    ("footer", "Footer"),
                    ("social", "Social Links"),
                    ("faq", "FAQ"),
                ],
                max_length=40,
            ),
        ),
    ]
