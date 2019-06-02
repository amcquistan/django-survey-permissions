# Django Authentication Part 1: Sign Up, Login, Logout


### Introduction

This is the first article in a multipart series on using and implementing the Django authentication system.  To aid in the discussion and demonstration of the many features of Django authentication I will be building a survey application which I'll call Django Survey throughout these tutorials. 

Each article of this series will focus on a subset of the features that can be implemented using Django's authentication system.

* Django Authentication Part 1: Sign Up, Login, Reset Password, Logout
* Django Authentication Part 2: Groups and Permissions (creating groups, assigning permissions to groups, assigning people to groups, assigning permissions to users, protecting class views with Permission classes)
* Django Authentication Part 3: Email Registration and Password Resets
* Django Authentication Part 4: Integrating Django REST Framework


### Local Dev Enivironment Setup

To start off I create a Python3 virtual enviroment, activate it then, pip install django and django-widget-tweaks (widget-tweaks is used for controlling the way forms are endered).

```
python3 -m venv venv
source venv/bin/activate
(venv) $ pip install django django-widget-tweaks
```

After that I create a django_survey project, change directories into the resulting django_survey directory and, make a django app called survey.

```
(venv) $ django-admin startproject django_survey
cd django_survey
python manage.py startapp survey
```

By default the django.contrib.auth and django.contrib.contenttypes modules should be included in the INSTALLED_APPS list in the project's main settings module at django_survey/settings.py as well as the django.contrib.session.middleware.SessionMiddleware and django.contrib.auth.middleware.AuthenticationMiddleware modules in the MIDDLEWARE list. These modules provide all the standard django authenication and authorization functionality.

While I'm on the topic of including things in INSTALLED_APPS now would be a good time to add the survey applicaiton to the list of INSTALLED_APPS as well as widget_tweaks like so.

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
]
```

To finish their setup I must run their database migrations to generate the default sqlite database, db.sqlite, and all the associated database tables like so.

```
(venv) python manage.py migrate
```

### The Django Authentication Models

The first thing to get a grasp on when learning django authentication are the User, Permission, and Group classes which lives in django.contrib.auth.models and serves to associate a user with some persisted data about that user and any groups and permissions they have.

Below I've included the class diagrams for User as well as Permission and Group.

__SHOW CLASS DIAGRAMS__

### Registering New Users

The first thing that I need to do is add the ability to add users to the survey applicaiton.  In order to do this I will need to provide a view class as well as use a template for providing UI and a form for working with the data.

To start off I will create a new class named RegisterView in the survey/views.py module which subclasses django.views.View and define a `get` method for serving up a template with a register form plus a `post` view method for collecting the posted data and creating a registered user. Until I add a login view I am going to just leave a TODO in the RegisterView.post method so I remember to add a redirect to the login view. The form that I'm using is the, UserCreationForm, a django model from the auth module which contains fields for username, password1 and password2 which are all required fields plus it checks that password1 and password2 match.

```
# survey/views.py

from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, reverse

from django.views import View

class RegisterView(View):
    def get(self, request):
        return render(request, 'survey/register.html', { 'form': UserCreationForm() })

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # TODO: redirect to login

        return render(request, 'survey/register.html', { 'form': form })
```

Next I add a new urls.py module inside the survey application and provide it with a register url that uses the RegisterView class like so.

```
# survey/urls.py

from django.urls import path

from . import views

urlpatterns = [
  path('register/', views.RegisterView.as_view(), name='register'),
]
```

I also need to let the project know that this app has urls by including them in the main URLConf django_survey/urls.py

```
"""django_survey URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('survey.urls'))
]
```

Now its time to add a UI to collect form data in.  To accomplish this I create a templates directory inside the survey directory. Inside that templates directory I add another named survey and within that templates/survey directory I add the files base.html and register.html leaving me with a directory structure starting at survey app that looks as follows.

```
.
├── __init__.py
├── admin.py
├── apps.py
├── migrations
│   └── __init__.py
├── models.py
├── templates
│   └── survey
│       ├── base.html
│       └── register.html
├── tests.py
├── urls.py
└── views.py
```

Inside of base.html I add the master layout which will source the Bulma css framework and define a single content block.

```
<!-- base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
  <title>Django Survey</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.5/css/bulma.css">
  <script defer src="https://use.fontawesome.com/releases/v5.3.1/js/all.js"></script>
</head>
<body>
  {% block content %}

  {% endblock %}
</body>
</html>
```

Over in register I extend the base.html layout and load the widget_tweaks template template tags then define a form for collecting registeration data.

```
<!-- register.html -->
{% extends 'survey/base.html' %}
{% load widget_tweaks %}

{% block content %}

<section class="hero is-success is-fullheight">
  <div class="hero-body">
    <div class="container">
      <h1 class="title has-text-centered">
        Django Survey
      </h1>

      <div class="columns">
        <div class="column is-offset-2 is-8">
          <h2 class="subtitle">
            Register
          </h2>

          <form action="{% url 'register' %}" method="POST" autocomplete="off">
            {% csrf_token %}
    
            <div class="field">
              <label for="{{ form.username.id_for_label }}" class="label">
                Username
              </label>
              <div class="control">
                {{ form.username|add_class:"input" }}
              </div>
              <p class="help is-danger">{{ form.username.errors }}</p>
            </div>
    
            <div class="field">
              <label for="{{ form.password1.id_for_label }}" class="label">
                Password
              </label>
              <div class="control">
                {{ form.password1|add_class:"input" }}
              </div>
              <p class="help is-danger">{{ form.password1.errors }}</p>
            </div>
    
            <div class="field">
              <label for="{{ form.password2.id_for_label }}" class="label">
                Password Check
              </label>
              <div class="control">
                {{ form.password2|add_class:"input" }}
              </div>
              <p class="help is-danger">{{ form.password2.errors }}</p>
            </div>
    
            <div class="field">
              <div class="control">
                <button class="button is-link">Submit</button>
              </div>
            </div>
          </form>
        </div>
      </div>

    </div>
  </div>
</section>

```

### User Login and Logout

Now that I have the ability to register a user I need to add in the ability to authenticate them.  To do this I'm going to first show the low level implementation that requires building my own LoginView class and directly uses the authenticate and login helper methods of the django.contrib.auth module then, I'm going to show a better way using the built in LoginView class from the django.contrib.auth module.

__Low Level Approach (Build Your Own)__

Back in survey/views.py I add another class view named LoginView which again provides a get method for serving up a login template and form as well as a post method for using form data to authenticate / login a user. Similar to the RegisterView class I'm using another form named AuthenticationForm which also comes from the auth module and contains the fields username and password. This AuthenticationForm does some pretty awesome stuff behind the scenes for us if you ask it nicely.

I'm actually going to break up this low level build it yourself section into really low level and moderately low level. To begin with I'll so the really low level which is as follows.

```
# survey/views.py

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, reverse

from django.views import View

class RegisterView(View):
    def get(self, request):
        return render(request, 'survey/register.html', { 'form': UserCreationForm() })

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect(reverse('login'))

        return render(request, 'survey/register.html', { 'form': form })


class LoginView(View):
    def get(self, request):
        return render(request, 'survey/login.html', { 'form':  AuthenticationForm })

    # really low level
    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data.get('username'),
                password=form.cleaned_data.get('password')
            )

            if user is None:
                return render(
                    request,
                    'survey/login.html',
                    { 'form': form, 'invalid_creds': True }
                )

            try:
                form.confirm_login_allowed(user)
            except ValidationError:
                return render(
                    request,
                    'survey/login.html',
                    { 'form': form, 'invalid_creds': True }
                )
            login(request, user)

            return redirect(reverse('profile'))


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        surveys = Survey.objects.filter(created_by=request.user).all()
        assigned_surveys = SurveyAssignment.objects.filter(assigned_to=request.user).all()

        context = {
          'surveys': surveys,
          'assigned_surveys': assigned_surveys
        }

        return render(request, 'survey/profile.html', context)
```

As mentioned earlier the LoginView.get method will simply render a template with a form which is pretty common stuff so, I'd like to focus more on the post method here. The first thing that occurs in LoginView.post is the AuthenicationForm is instantiated passing it the entire request object followed by just the request.POST dict to data. Then the form is checked for valid data using the is_valid method. 

After checking the forms validity I use the auth module's built in authenticate function passing it the request object as well as the username and password for the validated form data. The result of calling authenticate will either be an instance of the matched User object or None. If an object instance is returned then I proceed on to check that the user is active using the AuthenticationForm.confirm_login_allowed method which will raise a ValidationError if User.is_active is False.

If all is still well I go on to call another of the auth module's built in functions named login(...) passing it the request and authenticated user. This function associates the user with the session. At this point I redirect the user to the profile view that I have included beneath the LoginView class which returns the profile.html template along with a user's assigned surveys and the ones they've created.

```
# survey/urls.py

from django.urls import path

from . import views

urlpatterns = [
  path('register/', views.RegisterView.as_view(), name='register'),
  path('login/', views.LoginView.as_view(), name='login'),
  path('profile/', views.ProfileView.as_view(), name='profile'),
]
```

Next up is to create a login.html template file which will live in survey/templates/survey directory and contain a form for collecting the username and password needed for loggin in.

```
<!-- login.html -->
{% extends 'survey/base.html' %}
{% load widget_tweaks %}

{% block content %}

<section class="hero is-success is-fullheight">
  <div class="hero-body">
    <div class="container">
      <h1 class="title has-text-centered">
        Django Survey
      </h1>

      <div class="columns">
        <div class="column is-offset-2 is-8">
          <h2 class="subtitle">
            Login
          </h2>

          <form action="{% url 'login' %}" method="POST">
            {% csrf_token %}
    
            <div class="field">
              <label for="{{ form.username.id_for_label }}" class="label">
                Username
              </label>
              <div class="control">
                {{ form.username|add_class:"input" }}
              </div>
              <p class="help is-danger">{{ form.username.errors }}</p>
            </div>
    
            <div class="field">
              <label for="{{ form.password.id_for_label }}" class="label">
                Password
              </label>
              <div class="control">
                {{ form.password|add_class:"input" }}
              </div>
              <p class="help is-danger">{{ form.password.errors }}</p>
            </div>
    
            <div class="field">
              <div class="control">
                <button class="button is-link">Submit</button>
              </div>
            </div>
          </form>
        </div>
      </div>

    </div>
  </div>
</section>

{% endblock %}
```

While I'm doing template work I should add in a simple profile.html template that is being redirected to after successful login and displays a welcome message to the user along with a list for their created surveys as well as those that have been assigned to them.

```
<!-- profile.html -->
{% extends 'survey/base.html' %}
{% load widget_tweaks %}

{% block content %}

<section class="section">

  <div class="container">
    <h1 class="title has-text-centered">
      Django Survey
    </h1>

    <div class="columns">
      <div class="column is-offset-2 is-8">
        <h2 class="subtitle is-size-3">
          Welcome {{ request.user.username }}
        </h2>

        <h3 class="subtitle">Surveys You've Created</h3>
        <div class="content">
          <ul>
            {% for survey in surveys %}
            <li><a href="">{{ survey.title }}</a></li>
            {% endfor %}
          </ul>
        </div>

        <h3 class="subtitle">Surveys You've Been Assigned</h3>
        <div class="content">
          <ul>
            {% for assigned_survey in assgined_surveys %}
            <li><a href=""></a>{{ assigned_survey.survey.title }}</li>
            {% endfor %}
          </ul>
        </div>

      </div>
    </div>

  </div>

</section>

{% endblock %}
```

__Logout__

Ok, I'm able to log users into the application now using some of the more lower level mechanisms of the django.contrib.auth module but, as I mentioned earlier there are actually better, more abstracted, ways of doing this. I'd like to move on to showing some of these niceties but, in order to do that I need to be able to log people out first.  Turns out this is drop dead simple.

To log a user out I can use the LogoutView from the django.contrib.auth.views module inside the survey/urls.py module like so.

```
# survey/urls.py

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
  path('register/', views.RegisterView.as_view(), name='register'),
  path('login/', views.LoginView.as_view(), name='login'),
  path('profile/', views.ProfileView.as_view(), name='profile'),
  path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
```

To use this LogoutView I also need to add a new config variable in the project's settings module at django_survey/settings.py which tells the LogoutView where to redirect the user to when they have been logged out. This new config settings is shown below.

```
# settings.py

... skipping to the bottom

# custom
LOGOUT_REDIRECT_URL='/login/'
```

I should also include a navbar in base.html which will show either a logout button if they are authenticated or if not authenticated a pair of login and register buttons.  I can tell if a user is authenticated based off the user.is_authenticated property which is attached to the request object present in all templates and view classes. I am also going to use this time to add navbar links for the profile view and a yet to be defined create survey view. Both of these items should only be present for authenticated users.

```
<!-- base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
  <title>Django Survey</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.5/css/bulma.css">
  <script defer src="https://use.fontawesome.com/releases/v5.3.1/js/all.js"></script>
</head>
<body>
  <nav class="navbar" role="navigation" aria-label="main navigation">
    <div class="navbar-brand">
      <a class="navbar-item" href="/">
        Django Survey
      </a>
  
      <a role="button" class="navbar-burger burger" aria-label="menu" aria-expanded="false" data-target="navbarBasicExample">
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
      </a>
    </div>

    <div id="navbar-menu" class="navbar-menu">
      {% if request.user.is_authenticated %}
      <div class="navbar-start">
        <a class="navbar-item" href="{% url 'profile' %}">
          Profile
        </a>
        <!-- update this later -->
        <a class="navbar-item" href="#">
          Create Survey
        </a>
      </div>
      {% endif %}

      <div class="navbar-end">
        <div class="navbar-item">
          {% if request.user.is_authenticated %}
          <a class="button is-info" href="{% url 'logout' %}">Logout</a>
          {% else %}
          <div class="buttons">
            <a class="button is-primary" href="{% url 'register' %}">
              <strong>Sign up</strong>
            </a>
            <a class="button is-light" href="{% url 'login' %}">
              Log in
            </a>
          </div>
          {% endif %}
        </div>
      </div>
    </div>
  </nav>

  {% block content %}

  {% endblock %}
</body>
</html>
```

__Alternative Low Level Approach (Build Your Own)__

This alternative approach to building my own LoginView class will utilize more of the awesome sauce baked into the AuthenticationForm. Specifically, I am going to use the AuthenticationForm.clean method to authenticate the user and check that User.is_active field is True signifying they can login. Afterwards I retreive the user from the form using get_user along with the previously seen login(...) method.  The old LoginView.post method is commented out and left in for reference.

```
# survey/views.py

... only showing LoginView for brevity

class LoginView(View):
    def get(self, request):
        return render(request, 'survey/login.html', { 'form':  AuthenticationForm })

    # really low level
    # def post(self, request):
    #     form = AuthenticationForm(request, data=request.POST)
    #     if form.is_valid():
    #         user = authenticate(
    #             request,
    #             username=form.cleaned_data.get('username'),
    #             password=form.cleaned_data.get('password')
    #         )

    #         if user is None:
    #             return render(
    #                 request,
    #                 'survey/login.html',
    #                 { 'form': form, 'invalid_creds': True }
    #             )

    #         try:
    #             form.confirm_login_allowed(user)
    #         except ValidationError:
    #             return render(
    #                 request,
    #                 'survey/login.html',
    #                 { 'form': form, 'invalid_creds': True }
    #             )
    #         login(request, user)

    #         return redirect(reverse('profile'))

    #     return render(request, 'survey/login.html', { 'form': form })


    # low level but, using AuthenticationForm.clean for authentication
    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            try:
                form.clean()
            except ValidationError:
                return render(
                    request,
                    'survey/login.html',
                    { 'form': form, 'invalid_creds': True }
                )

            login(request, form.get_user())

            return redirect(reverse('profile'))

        return render(request, 'survey/login.html', { 'form': form })
```

Note that this has drastically cut down on the amount of code required to accomplish this task. However, as you will soon see, this can be reduced even further by using the builtin LoginView from the django.contrib.auth.views module similar to what was done with the LogoutView. I will demonstrate this next.

__High Level Approach (Using the Django LoginView)__

Over in survey/urls.py I locate the login url path and replace the custom built views.LoginView class with the django.contrib.auth.views.LoginView and assign a parameter named template_name within the .as_view(...) method to the same survey/login.html template used previously.

```
# survey/urls.py

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
  path('register/', views.RegisterView.as_view(), name='register'),
  path('login/', auth_views.LoginView.as_view(template_name='survey/login.html'), name='login'),
  path('profile/', views.ProfileView.as_view(), name='profile'),
  path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
```

Also, back in django_survey/settings.py I need to add another configuration variable which tells this builtin LoginView class where to redirect users after login as shown below.

```
# settings.py

... skipping to the bottom

# custom
LOGOUT_REDIRECT_URL='/login/'
LOGIN_REDIRECT_URL='/profile/'
```

And ... whola! Magical right?! It probably go without saying but ... this should definitely be the preferred way of handling authentication.

### Creating Surveys

Moving on I will continue to build the actual survey creation and survey taking functionality along with the ability to assign them to survey takers.  First thing should be to build out the data models over in survey/models.py as shown below.

### Password Resets



```
# models.py

from django.db import models
from django.conf import settings

class Survey(models.Model):
    title = models.CharField(max_length=200)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='surveys'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Question(models.Model):
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    question = models.ForeignKey(
        Survey, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions'
    )


class Choice(models.Model):
    text = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    question = models.ForeignKey(
        Question, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='choices'
    )


class SurveyAssignment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    survey = models.ForeignKey(
        Survey,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='survey_assignments'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_surveys_to'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_surveys'
    )


class SurveyResponse(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    survey_assigned = models.ForeignKey(
        SurveyAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='survey_responses'
    )
    question = models.ForeignKey(
        Question, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='question_responses'
    )
    choice = models.ForeignKey(
        Choice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='choices_selected'
    )
```

I'm intentionally skipping a lot of the details on these models in hopes that they are fairly straight forward to the reader. If not please consult the [Django docs](https://docs.djangoproject.com/en/2.2/), particularly the [polls tutorial](https://docs.djangoproject.com/en/2.2/intro/tutorial01/).  

In short, a user (django.contrib.auth.models.User) can create a survey (survey.models.Survey). Each survey can have one or more questions (survey.models.Question) and each question can have one or more choice (survey.models.Choice). A survey can be assigned to one or more users which are captured in the database as a survey.models.SurveyAssignment. A survey assignment is linked to a collection of responses (survey.models.SurveyResponse) objects mapping each survey's question to a choice selected by the assigned user. 

After migrating the data models to the database, using the commands below, I can build out a view class for creating a survey and pair it to a template.  

```
(venv) $ python manage.py makemigrations
(venv) $ python manage.py migrate
```

Over in survey/views.py I add a new view class named SurveyCreateView and configure it to be only accessible by authenticated users by having it inherit from django.contrib.auth.mixins.LoginRequiredMixin. I also update the ProfileView class to be authentication protected as well.

In order to be able to properly utilize the LoginRequiedMixin I must include another configuration variable named LOGIN_URL which tells the mixin where to send unauthenticated users when they try to access protected views. If an unauthenticated user gets redirected to the login view a query parameter named next is appended to the LOGIN_URL path which is used to conviently send the user back to the original protected view that redirected the user to the login view.

```
# settings.py

... skipping to the bottom

# custom
LOGOUT_REDIRECT_URL='/login/'
LOGIN_REDIRECT_URL='/profile/'
LOGIN_URL='/login/'
```

The SurveyCreateView class again has a get method which serves up a template named create_survey.html which provides a UI with a form for collecting the data necessary to create a survey (title, questions, choices and, assgined users). Additionally, SurveryCreateView contains a post method that grabs the form data, creates a Survey instance along with the associated relations and persists it to the database before redirecting the user to the profile page. Shown below is the updated views.py module.

```
# survey/views.py

import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, reverse

from django.views import View

from .forms import SurveyCreateForm
from .models import Survey

... skipping down to SurveyCreateView for brevity


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
            question = Question.objects.create(text=question_data['text'], survey=survey)
            for choice_data in question_data['choices']:
                Choice.objects.create(text=choice_data['text'], question=question)
              
        for assignee in assignees:
            assigned_to = User.objects.get(pk=int(assignee))
            SurveyAssignment.objects.create(
                survey=survey,
                assigned_by=request.user,
                assigned_to=assigned_to
            )

        return redirect(reverse('profile'))
```

Next I update the surveys/urls.py field to include this new SurveyCreateView view class and associate it with the url path surveys/create/ like so.

```
# survey/urls.py

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
  path('register/', views.RegisterView.as_view(), name='register'),
  path('login/', auth_views.LoginView.as_view(template_name='survey/login.html'), name='login'),
  path('profile/', views.ProfileView.as_view(), name='profile'),
  path('logout/', auth_views.LogoutView.as_view(), name='logout'),
  path('surveys/create/', views.SurveyCreateView.as_view(), name='survey_create'),
]
```

With those changes in place I can head back over to surveys/base.html and update the Create Survey navbar link item with this new url path.

```
<!-- base.html -->

... omitting all but the profile and create survey link for brevity

  {% if request.user.is_authenticated %}
  <div class="navbar-start">
    <a class="navbar-item" href="{% url 'profile' %}">
      Profile
    </a>
    <a class="navbar-item" href="{% url 'survey_create' %}">
      Create Survey
    </a>
  </div>
  {% endif %}

```

The last peice of this part is to build out the create_survey.html template.  This template will be a bit involved as I'll be taking a little foray into JavaScript land, in particular using my favorite JS tool Vue.js to dynamically add questions and their choices. Furthermore, since dynamic javascript driven UI isn't really the focus of this article on django authenitication I'll be skimping a bit on the details.

Gettings started, I make a new template named create_survey.html within the templates/surveys directory then at the top I extend the surveys/base.html layout template, source the vue.js script, then make a form pointed to post data to the SurveyCreateView defined above. 

```
{% extends 'survey/base.html' %}

{% block content %}
<script src="https://cdn.jsdelivr.net/npm/vue@2.6.10/dist/vue.js"></script>
<section class="section">
  <div class="container">
    <h1 class="title has-text-centered">
      Django Survey
    </h1>

    <div class="columns">
      <div class="column is-offset-2 is-8">
        <h2 class="subtitle">
          Create Survey
        </h2>

        <form action="{% url 'survey_create' %}" id="survey-form" method="POST">
          {% csrf_token %}
          <div class="field">
            <label for="title" class="label">
              Title
            </label>
            <div class="control">
              <input type="text" class="input" name="title" id="title">
            </div>
            <p class="help is-danger">{{ title_error }}</p>
          </div>

          <div class="field">
            <label for="" class="label">Assignees</label>
            <div class="control">
              <div class="select is-multiple">
                <select multiple size="4" name="assignees">
                  {% for user in users %}
                  <option value="{{ user.id }}">{{ user.username }}</option>
                  {% endfor %}
                </select>
              </div>
              <p class="help is-danger">{{ assignee_error }}</p>
            </div>
          </div>

          <div class="field">
            <label for="" class="label">Questions</label>
            <div class="control">
              <a @click.stop="addQuestion" class="button is-info is-small">
                <span class="icon">
                  <i class="fas fa-plus"></i>
                </span>
                <span>Add Question</span>
              </a>
            </div>
            <p class="help is-danger">{{ questions_error }}</p>
          </div>
          <ol>
            <li 
            	style="padding-bottom: 25px;" 
            	v-for="question in questions" 
            	:key="'question_' + question.id">
              <div class="field is-grouped">
                <label :for="'question_' + question.id" class="label">
                </label>
                <div class="control is-expanded">
                  <input type="text" class="input" v-model="question.text">
                </div>
                <div class="control">
                  <a @click.stop="removeQuestion(question)" class="button is-danger">
                    <span class="icon is-small">
                      <i class="fas fa-times"></i>
                    </span>
                  </a>
                </div>
              </div>
              <div style="margin-left: 30px;">
                <div class="field">
                  <label for="" class="label">Choices</label>
                  <div class="control">
                    <a @click.stop="addChoice(question)" class="button is-success is-small">
                      <span class="icon is-small">
                        <i class="fas fa-plus"></i>
                      </span>
                      <span>Add Choice</span>
                    </a>
                  </div>
                </div>

                <ol>
                  <li v-for="choice in question.choices" :key="'choice_' + choice.id">
                    <div class="field is-grouped">
                      <label :for="'choice_' + choice.id" class="label">
                      </label>
                      <div class="control is-expanded">
                        <input type="text" class="input" v-model="choice.text">
                      </div>
                      <div class="control">
                        <a @click.stop="removeChoice(question, choice)" class="button is-danger">
                          <span class="icon is-small">
                            <i class="fas fa-times"></i>
                          </span>
                        </a>
                      </div>
                    </div>
                  </li>
                </ol>

              </div>
              <input 
              	v-if="validQuestion(question)" 
              	type="hidden" 
              	name="questions" 
              	:value="serializeQuestion(question)">
            </li>
          </ol>
          <div class="field">
            <div class="control">
              <button class="button is-success">Submit</button>
            </div>
          </div>
        </form>
      </div>
    </div>

  </div>

</section>

<script>
new Vue({
  delimiters: ['[[', ']]'],
  el: '#survey-form',
  data: {
    questionId: 1,
    choiceId: 1,
    questions: []
  },
  methods: {
    addQuestion: function() {
      var _this = this;
      _this.questions.push({
        id: _this.questionId,
        text: '',
        choices: [{
          id: _this.choiceId,
          text: ''
        }]
      });
      _this.questionId++;
      _this.choiceId++;
    },
    removeQuestion: function(question) {
      var questions = this.questions.slice();
      var idx = questions.indexOf(question);
      questions.splice(idx, 1)
      this.questions = questions;
    },
    addChoice: function(question) {
      var _this = this;
      question.choices.push({
        id: _this.choiceId,
        text: ''
      });
      var idx = _this.questions.indexOf(question);
      var questions = _this.questions.slice();
      questions[idx] = question;
      _this.questions = questions;
      _this.choiceId++;
    },
    removeChoice: function(question, choice) {
      var questions = this.questions.slice();
      var qIdx = questions.indexOf(question);
      var cIdx = question.choices.indexOf(choice);
      question.choices.splice(cIdx, 1);
      questions[qIdx] = question;
      this.questions = questions;
    },
    serializeQuestion: function(question) {
      var q = Object.assign({}, question);
      q.choices = q.choices.filter(function(c){
        return Boolean(c.text);
      });
      return JSON.stringify(q);
    },
    validQuestion: function(question) {
      var valid = Boolean(question.text);
      if (valid) {
        var choices = question.choices.filter(function(c) {
          return Boolean(c.text);
        });
        valid = Boolean(choices);
      }
      return valid;
    }
  },
  mounted: function() {
    this.addQuestion()
  }
})
</script>

{% endblock %}
```

The jist of the above template, and in particular, the Vue.js code is to provide an ability for a user to add and remove questions which each question having the ability to have choices added and removed. All the question data including their availble choices are serialized to JSON strings placed into an array of hidden inputs and submitted with the survey title and a selection of assigned users in the form.


### Conclusion

In this article I have demonstrated how to implement basic user registration, login, and logout for the Django Survey demo application. Building on this ability to authenticate a user I've shown how to restrict access to view classes to only authenticated users. In the next article I will be demonstrating how to use groups as well as assign permissions on a per Survey object instance to restrict who can view a survey and provide their own input as well as who can view a survey's resutls. 


TODO:

* create a group for each survey
* Assign permission to that survey's group to view results
* add people to that group
* build a view to see the survey results for survey writer and people in the survey's group of viewers
