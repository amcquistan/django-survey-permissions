# Django Authentication Part 2: Object Permissions with Django Guardian

### Introduction

This is the second article in a multipart series on using and implementing the Django authentication system.  To aid in the discussion and demonstration of the many features of Django authentication I will be building a survey application which I'll call Django Survey throughout these tutorials. 

Each article of this series will focus on a subset of the features that can be implemented using Django's authentication system.

* Django Authentication Part 1: Sign Up, Login, Reset Password, Logout
* Django Authentication Part 2: Groups and Permissions (creating groups, assigning permissions to groups, assigning people to groups, assigning permissions to users, protecting class views with Permission classes)
* Django Authentication Part 3: Email Registration and Password Resets
* Django Authentication Part 4: Integrating Django REST Framework

In this article I will be focusing on using the popular Django Guardian package to add permissions at the object instance level for individual users and groups of users.  These permissions will be used to control who can view and take a survey as well as who can view survey results.

### Installing and Settings Up Django Guardian
To install Django Guardian I simply use pip as shown below.  

```
pip install django-guardian
```

After than I need to make the project aware of guardian's existence by adding it to the list of INSTALLED_APPS.

```
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'survey.apps.SurveyConfig',
    'widget_tweaks',
    'guardian',
]
```

Then add guardian.backends.ObjectPermissionBackend to the AUTHENTICATION_BACKENDS list so it looks like this.

```
AUTHENTICATION_BACKENDS = [
  'django.contrib.auth.backends.ModelBackend',
  'guardian.backends.ObjectPermissionBackend',
]
```

After those two setitngs update the last thing to do is run the migrations.

```
(venv) python manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, guardian, sessions, survey
Running migrations:
  Applying guardian.0001_initial... OK
```

### Assiging Permissions to Take a Survey

With Django Guardian integrated into the project I can now starting protecting the SurveyAssignment model with specific permissions. By default Django gives the Survey model already has the view permission associated with it, in fact, the full set of default permissions for Survey are:
* add_surveyassignment
* change_surveyassginment
* view_surveyassignment
* delete_surveyassignment

However, in my case I want to apply this permission to the user's who have been assigned to take them at the object instance level rather than the broad model (aka class) level.  This is where Django Guardian comes in. To accomplish this I need to update the SurveyCreateView.post method to give the view_surveyassignment permission to the assigned users using the assign_perm(...) function from the guardian.shortcuts module.

```
# survey/views.py

import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, reverse

from django.views import View

# new assign_perm guardian function import
from guardian.shortcuts import assign_perm

from .models import Survey, Question, Choice, SurveyAssignment


... skipping down to SurveyCreateView

class SurveyCreateView(LoginRequiredMixin, View):
    def get(self, request):
        users = User.objects.all()
        return render(request, 'survey/create_survey.html', {'users': users})
    
    def post(self, request):
        data = request.POST
        
        title = data.get('title')
        questions_json = data.getlist('questions')
        assignees = data.getlist('assignees')
        valid = True
        context = {}
        if not title:
            valid = False
            context['title_error'] = 'title is required'

        if not questions_json:
            valid = False
            context['questions_error'] = 'questions are required'
            
        if not assignees:
            valid = False
            context['assignees_error'] = 'assignees are required'
        
        if not valid:
            context['users'] = User.objects.all()
            return render(request, 'survey/create_survey.html', context)
            
        survey = Survey.objects.create(title=title, created_by=request.user)
        for question_json in questions_json:
            question_data = json.loads(question_json)
            question = Question.objects.create(
            		text=question_data['text'],
            		survey=survey
            )
            for choice_data in question_data['choices']:
                Choice.objects.create(
                		text=choice_data['text'],
                		question=question
                )
              
        for assignee in assignees:
            assigned_to = User.objects.get(pk=int(assignee))
            assigned_survey = SurveyAssignment.objects.create(
                survey=survey,
                assigned_by=request.user,
                assigned_to=assigned_to
            )
            assign_perm('view_surveyassginment', assigned_to, assigned_survey)

        return redirect(reverse('profile'))


```

The key to this change is the assign_perm('view_surveyassginment', assigned_to, assigned_survey) which specifically assigns the 'view_surveyassginment' permission to the users for the instance of the survey assginment being created.  However, this will only protect the newly created surveys. To update any existing survey's that have been previously created I will need to make a django migration to assign this object instance level permission to the existing survey's and assigned users.

To start I create an empty migration script.

```
(venv) python manage.py makemigrations --empty survey
Migrations for 'survey':
  survey/migrations/0004_auto_20190602_1835.py
```

I find the newly generated migration file, survey/migrations/0004_auto_20190602_1835.py, and open it in my editor.  I go on to populate the migration with the following.

```
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
```

Next I'd like to add the ability for asigned survey takers to comnplete their surveys. To do this I'll add the SurveyAssignmentView complete with a get method that serves a survey_assignment.html template that displays their assigned survey that they user can fill out. To complement the get method will be post method that will accept posted survey response data and save it to the database. 

Given that I've already established the requirement that a user must be assigned a survey in order to view and, thus complete a survey response, I will also need to guard the SurveyAssignmentView view class which checks to make sure that the requested survey is capable of being viewed by the authenticated user requesting that page.

To guard the SurveyAssignmentView I make it inherit from guardian.mixins.PermissionRequiredMixin which checks that the requesting user is logged in then checks for a specific permission based off how the class is configured.  If either of these checks fail then the user is redirected to the login view. Below is the new SurveyAssignmentView.

```
# views.py

... skipping down to SurveyAssignmentView

class SurveyAssignmentView(PermissionRequiredMixin, View):
    permission_required = 'survey.view_surveyassignment'

    def get_object(self):
        self.obj = get_object_or_404(SurveyAssignment, pk=self.kwargs['assignment_id'])
        return self.obj

    def get(self, request, assignment_id):
        # survey = Survey.objects.get(pk=survey_id)
        return render(request, 'survey/survey_assignment.html', {'survey_assignment': self.obj})

    def post(self, request, assignment_id):
        context = {'validation_error': ''}
        save_id = transaction.savepoint()
        try: 
            for question in self.obj.survey.questions.all():
                question_field = f"question_{question.id}"
                if question_field not in request.POST:
                    context['validation_error'] = 'All questions require an answer'
                    break
                
                choice_id = int(request.POST[question_field])
                choice = get_object_or_404(Choice, pk=choice_id)
                SurveyResponse.objects.create(
                    survey_assigned=self.obj,
                    question=question,
                    choice=choice
                )

            if context['validation_error']:
                transaction.savepoint_rollback(save_id)
                return render(request, 'survey/survey_assignment.html', context)

            transaction.savepoint_commit(save_id)
        except:
            transaction.savepoint_rollback(save_id)

        return redirect(reverse('profile'))
```

In order to properly configure the SurveyAssignmentView to utilize PermissionRequiredMixin I must set permission_required = 'survey.view_surveyassignment' and provide and implementation of get_object. Under the hood the PermissionRequiredMixin calls its check_permissions method which (suprise suprise) checks the permission specified against the SurveyAssigment object and either returns True and continues onto the request handler or returns False and redirects to the settings.LOGIN_URL specified earlier.

For completeness I have included the survey_assignment.html template below. It simply displays a form of questions and choice radio buttons.

```
<!-- survey_assignment.html -->
{% extends 'survey/base.html' %}

{% block content %}

<section class="section">
  <div class="container">
    <h1 class="title has-text-centered">
      Django Survey
    </h1>

    <div class="columns">
      <div class="column is-offset-2 is-8">
        <h2 class="subtitle is-size-4">
          Survey: {{ survey_assignment.survey.title }}
        </h2>
        {% if validation_error %}
          <p>{{ validation_error }}</p>
        {% endif %}
        <form action="{% url 'survey_assignment' survey_assignment.id %}" method="POST">
          {% csrf_token %}
          <ol>
            {% for question in survey_assignment.survey.questions.all %}
            <li style="margin-bottom: 20px;">
              {{ question.text }}
              
              {% for choice in question.choices.all %}
              <div class="control">
                <label for="choice_{{choice.id}}" class="radio">
                  <input id="choice_{{choice.id}}" type="radio" name="question_{{question.id}}" value="{{choice.id}}" required>
                  {{ choice.text }}
                </label>
              </div>
              {% endfor %}
              
            </li>
            {% endfor %}
          </ol>
          {% if survey_assignment.survey_responses.count == 0 %}
          <div class="field">
            <div class="control">
              <button class="button is-link">Submit</button>
            </div>
          </div>
          {% else %}
          <p>You've already completed this survey</p>
          {% endif %}
        </form>

      </div>
    </div>

  </div>

</section>

{% endblock %}
```

### Assign Permissions to View Survey Results

add SurveyResultsView class to display survey results

show how to protect the SurveyResultsView class to only those who are the survey creator or those in the survey results viewing group

### Conclusion

