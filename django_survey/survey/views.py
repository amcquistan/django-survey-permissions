# survey/views.py

import json
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect, reverse, get_object_or_404

from django.views import View

from guardian.conf import settings as guardian_settings
from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import assign_perm, get_objects_for_user

from .models import Survey, Question, Choice, SurveyAssignment, SurveyResponse
from .tokens import user_tokenizer
from .forms import RegistrationForm

class RegisterView(View):
    def get(self, request):
        return render(request, 'survey/register.html', { 'form': RegistrationForm() })

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_valid = False
            user.save()
            token = user_tokenizer.make_token(user)
            user_id = urlsafe_base64_encode(force_bytes(user.id))
            url = 'http://localhost:8000' + reverse('confirm_email', kwargs={'user_id': user_id, 'token': token})
            message = get_template('survey/register_email.html').render({
              'confirm_url': url
            })
            mail = EmailMessage('Django Survey Email Confirmation', message, to=[user.email], from_email=settings.EMAIL_HOST_USER)
            mail.content_subtype = 'html'
            mail.send()

            return render(request, 'survey/login.html', {
              'form': AuthenticationForm(),
              'message': f'A confirmation email has been sent to {user.email}. Please confirm to finish registering'
            })

        return render(request, 'survey/register.html', { 'form': form })

# this view class was replaced by django.contrib.auth.views.LoginView
class LoginView(View):
    def get(self, request):
        return render(request, 'survey/login.html', { 'form':  AuthenticationForm() })

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


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        surveys = Survey.objects.filter(created_by=request.user).all()
        assigned_surveys = SurveyAssignment.objects.filter(assigned_to=request.user).all()
        survey_results = get_objects_for_user(request.user, 'can_view_results', klass=Survey)

        context = {
          'surveys': surveys,
          'assgined_surveys': assigned_surveys,
          'survey_results': survey_results
        }

        return render(request, 'survey/profile.html', context)


class SurveyCreateView(LoginRequiredMixin, View):
    def get(self, request):
        users = User.objects.all()
        return render(request, 'survey/create_survey.html', {'users': users})
    
    def post(self, request):
        data = request.POST
        
        title = data.get('title')
        questions_json = data.getlist('questions')
        assignees = data.getlist('assignees')
        reviewers = data.getlist('reviewers')
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

        perm = Permission.objects.get(codename='view_surveyassignment')
        for assignee in assignees:
            assigned_to = User.objects.get(pk=int(assignee))
            assigned_survey = SurveyAssignment.objects.create(
                survey=survey,
                assigned_by=request.user,
                assigned_to=assigned_to
            )
            assign_perm(perm, assigned_to, assigned_survey)

        group = Group.objects.create(name=f"survey_{survey.id}_result_viewers")
        assign_perm('can_view_results', group, survey)
        request.user.groups.add(group)
        request.user.save()

        for reviewer_id in reviewers:
            reviewer = User.objects.get(pk=int(reviewer_id))
            reviewer.groups.add(group)
            reviewer.save()

        return redirect(reverse('profile'))


class SurveyManagerView(UserPassesTestMixin, View):
  
    def test_func(self):
        self.obj = Survey.objects.get(pk=self.kwargs['survey_id'])
        return self.obj.created_by.id == self.request.user.id

    def get(self, request, survey_id):

        users = User.objects.exclude(Q(pk=request.user.id) | Q(username=guardian_settings.ANONYMOUS_USER_NAME))
        assigned_users = {
            sa.assigned_to.id 
            for sa in SurveyAssignment.objects.filter(survey=self.obj)
        }

        context = {
          'survey': self.obj,
          'available_assignees': [u for u in users if u.id not in assigned_users],
          'available_reviewers': [u for u in users if not u.has_perm('can_view_results', self.obj)]
        }
        return render(request, 'survey/manage_survey.html', context)

    def post(self, request, survey_id):
        assignees = request.POST.getlist('assignees')
        reviewers = request.POST.getlist('reviewers')
        
        perm = Permission.objects.get(codename='view_surveyassignment')
        for assignee_id in assignees:
            assigned_to = User.objects.get(pk=int(assignee_id))
            assigned_survey = SurveyAssignment.objects.create(
                survey=self.obj,
                assigned_by=request.user,
                assigned_to=assigned_to
            )
            assign_perm(perm, assigned_to, assigned_survey)
      
        group = Group.objects.get(name=f"survey_{self.obj.id}_result_viewers")
        for reviewer_id in reviewers:
            reviewer = User.objects.get(pk=int(reviewer_id))
            reviewer.groups.add(group)
            reviewer.save()

        return redirect(reverse('profile'))


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


class QuestionViewModel:
    def __init__(self, text):
        self.text = text
        self.choices = []

    def add_survey_response(self, survey_response):
        for choice in self.choices:
            if choice.id == survey_response.choice.id:
                choice.responses += 1
                break


class ChoiceResultViewModel:
    def __init__(self, id, text, responses=0):
        self.id = id
        self.text = text
        self.responses = responses


class SurveyResultsView(PermissionRequiredMixin, View):
    permission_required = 'survey.can_view_results'

    def get_object(self):
        self.obj = get_object_or_404(Survey, pk=self.kwargs['survey_id'])
        return self.obj

    def get(self, request, survey_id):
        questions = []
        for question in self.obj.questions.all():
            question_vm = QuestionViewModel(question.text)
            for choice in question.choices.all():
                question_vm.choices.append(ChoiceResultViewModel(choice.id, choice.text))
            
            for survey_response in SurveyResponse.objects.filter(question=question):
                question_vm.add_survey_response(survey_response)
            
            questions.append(question_vm)

        for question in questions:
            print(question.text)
            for choice in question.choices:
                print(choice.text, choice.responses)
            print()

        context = {'survey': self.obj, 'questions': questions}
        
        return render(request, 'survey/survey_results.html', context)


class TestEmail(View):
    def get(self, request):
        user = User.objects.get(pk=9)
        token = user_tokenizer.make_token(user)
        user_id = urlsafe_base64_encode(force_bytes(user.id))
        url = 'http://localhost:8000' + reverse('confirm_email', kwargs={'user_id': user_id, 'token': token})
        message = get_template('survey/register_email.html').render({
          'confirm_url': url
        })
        mail = EmailMessage('Django Survey Email Confirmation', message, to=[user.email], from_email=settings.EMAIL_HOST_USER)
        mail.content_subtype = 'html'
        mail.send()
        return HttpResponse(f'email sent user_id = {user_id}, token = {token}')


class ConfirmRegistrationView(View):
    def get(self, request, user_id, token):
        user_id = force_text(urlsafe_base64_decode(user_id))
        
        user = User.objects.get(pk=user_id)

        context = {
          'form': AuthenticationForm(),
          'message': 'Registration confirmation error . Please click the reset password to generate a new confirmation email.'
        }
        if user and user_tokenizer.check_token(user, token):
            user.is_valid = True
            user.save()
            context['message'] = 'Registration complete. Please login'

        return render(request, 'survey/login.html', context)
