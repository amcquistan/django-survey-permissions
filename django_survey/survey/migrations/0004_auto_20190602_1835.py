# Generated by Django 2.2.1 on 2019-06-02 18:35

from django.conf import settings
from django.db import migrations

from guardian.shortcuts import assign_perm
from guardian.compat import get_user_model

def add_view_surveyassginemnt_perms(apps, schema_editor):
    SurveyAssignment = apps.get_model('survey', 'SurveyAssignment')
    survey_assignments = SurveyAssignment.objects.all()
    User = get_user_model()
    for assigned_survey in survey_assignments:
        assignee = assigned_survey.assigned_to
        user = User.objects.get(pk=assignee.id)
        if not user.has_perm('view_surveyassignment', assigned_survey):
            assign_perm('view_surveyassignment', user, assigned_survey)

class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0003_auto_20190601_0447'),
    ]

    operations = [
        migrations.RunPython(add_view_surveyassginemnt_perms)
    ]
