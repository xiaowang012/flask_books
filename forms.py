#coding=utf-8
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SelectField,DateField,FloatField,SubmitField,FileField
from wtforms.validators import AnyOf, DataRequired, EqualTo,Length, NumberRange
from flask_wtf.file import FileRequired,FileAllowed

#用户注册表单
class RegisterForms(FlaskForm):
    username = StringField('username',validators = [DataRequired('Username cannot be empty!'),Length(min=6,max=12,message = 'The username must be 6-12 characters long!')])
    password = PasswordField ('password',validators = [DataRequired('Password cannot be empty!'),Length(min=6,max=12,message = 'The password must be 6-12 characters long!')])
    password1 = PasswordField ('password1',validators = [DataRequired('Password1 cannot be empty!'),Length(min=6,max=12,message = 'The password must be 6-12 characters long!'),EqualTo('password',message = 'The entered passwords are inconsistent')])
    submit = SubmitField('submit')

#用户登录表单
class UserForms(FlaskForm):
    username = StringField('username',validators = [DataRequired('Username cannot be empty!'),Length(min=6,max=12,message = 'The username must be 6-12 characters long!')])
    password = PasswordField ('password',validators = [DataRequired('Password cannot be empty!'),Length(min=6,max=12,message = 'The password must be 6-12 characters long!')])
    submit = SubmitField('submit')

#民族信息列表
nations = ['汉族', '满族', '蒙古族', '回族', '藏族', '维吾尔族', '苗族', '彝族', '壮族', '布依族', '侗族', '瑶族', '白族', '土家族', '哈尼族', '哈萨克族', '傣族', '黎族', '傈僳族', '佤族', '畲族', '高山族', '拉祜族', '水族', '东乡族', '纳西族', '景颇族', '柯尔克孜族', '土族', '达斡尔族', '仫佬族', '羌族', '布朗族', '撒拉族', '毛南族', '仡佬族', '锡伯族', '阿昌族', '普米族', '朝鲜族', '塔吉克族', '怒族', '乌孜别克族', '俄罗斯族', '鄂温克族', '德昂族', '保安族', '裕固族', '京族', '塔塔尔族', '独龙族', '鄂伦春族', '赫哲族', '门巴族', '珞巴族', '基诺族']
class StudentsInfoForms(FlaskForm):
    #字段：id name sex date nation height	idCard PhoneNumber address teacher hobbies

    id = StringField('id',validators = [DataRequired('学号不能为空!'),Length(6,12,message = '学号长度为6-12位数字!')])
    name = StringField('name',validators = [DataRequired('姓名不能为空!')])
    sex = SelectField('sex',choices= [('male','男'),('female','女')])
    date = DateField('date',validators = [DataRequired('出生年月错误!')])
    nation = StringField('nation',validators = [DataRequired('民族不能为空!'),AnyOf(values = nations,message = '所填写的民族信息不在中华人民共和国56个民族之内!')])
    height = FloatField('height',validators= [DataRequired('身高信息不能为空!'),NumberRange(min = 1,max = 2,message = '身高不符合要求(1-2米)!')])
    idCard = StringField('idCard',validators = [DataRequired('身份证号码不能为空!'),Length(18,18,message = '身份证号码长度为18位!')])
    PhoneNumber = StringField('PhoneNumber',validators = [DataRequired('手机号码不能为空!'),Length(11,11,message = '手机号码长度为11位!')])
    address = StringField('address',validators = [DataRequired('家庭住址不能为空!')])
    teacher = StringField('teacher',validators = [DataRequired('班主任姓名不能为空!')])
    hobbies = StringField('hobbies',validators = [DataRequired('兴趣爱好不能为空!')])
    submit = SubmitField('提交')

#home界面查询书本的表单
class SearchIdForms(FlaskForm):
    book_name= StringField('book_name',validators = [DataRequired()])
    submit = SubmitField('submit')

#批量导入用户的表单
class UploadFileForms(FlaskForm):
    file = FileField('file',validators = [FileRequired(message = 'File cannot be empty!'),FileAllowed(['xlsx','xls'],message = 'File format error (XLSX/XLS only)!')])
    submit = SubmitField('submit')