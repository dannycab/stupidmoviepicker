"""
Flask-WTF forms for user authentication
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from auth import User

class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=80, message="Username must be between 3 and 80 characters")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required")
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=80, message="Username must be between 3 and 80 characters")
    ])
    email = EmailField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        Length(max=120, message="Email must be less than 120 characters")
    ])
    first_name = StringField('First Name', validators=[
        Length(max=100, message="First name must be less than 100 characters")
    ])
    last_name = StringField('Last Name', validators=[
        Length(max=100, message="Last name must be less than 100 characters")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Validate username is unique"""
        user = User.get_by_username(username.data)
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        """Validate email is unique"""
        user = User.get_by_email(email.data)
        if user:
            raise ValidationError('Email already registered. Please choose a different one.')

class ProfileForm(FlaskForm):
    """User profile editing form"""
    first_name = StringField('First Name', validators=[
        Length(max=100, message="First name must be less than 100 characters")
    ])
    last_name = StringField('Last Name', validators=[
        Length(max=100, message="Last name must be less than 100 characters")
    ])
    email = EmailField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        Length(max=120, message="Email must be less than 120 characters")
    ])
    submit = SubmitField('Update Profile')
    
    def __init__(self, original_email, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
    
    def validate_email(self, email):
        """Validate email is unique (except for current user)"""
        if email.data != self.original_email:
            user = User.get_by_email(email.data)
            if user:
                raise ValidationError('Email already registered. Please choose a different one.')

class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message="Current password is required")
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required"),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    new_password2 = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your new password"),
        EqualTo('new_password', message="Passwords must match")
    ])
    submit = SubmitField('Change Password')

class AdminUserForm(FlaskForm):
    """Admin form for managing users"""
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=80, message="Username must be between 3 and 80 characters")
    ])
    email = EmailField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        Length(max=120, message="Email must be less than 120 characters")
    ])
    first_name = StringField('First Name', validators=[
        Length(max=100, message="First name must be less than 100 characters")
    ])
    last_name = StringField('Last Name', validators=[
        Length(max=100, message="Last name must be less than 100 characters")
    ])
    is_admin = BooleanField('Administrator')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save User')
