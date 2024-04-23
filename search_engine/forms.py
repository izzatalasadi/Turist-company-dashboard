from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired,FileAllowed
from wtforms import SubmitField,TextAreaField
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Regexp, Email

class UploadForm(FlaskForm):
    file = FileField('Excel File', validators=[
        FileRequired(),
        FileAllowed(['xlsx'], 'Excel documents only.')])
    submit = SubmitField('Upload')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={"autocomplete": "username"})
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.'),
        Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*])',
               message='Password must contain a lowercase letter, an uppercase letter, a number, and a special character.')
    ], render_kw={"autocomplete": "current-password"})
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')
  
class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.'),
        Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*])',
               message='Password must contain a lowercase letter, an uppercase letter, a number, and a special character.')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile', validators=[Length(min=10, max=15)])
    bio = TextAreaField('Bio')
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    is_admin = BooleanField('Is Admin')
    submit = SubmitField('Add User')

class DeleteUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Delete User')

class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    profile_picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg','jpeg', 'png'])])
    mobile = StringField('Mobile', validators=[Length(min=10, max=15)])
    submit = SubmitField('Update')

class SearchForm(FlaskForm):
    search_query = StringField('Search')
    submit = SubmitField('Search')