import base64
import OpenSSL
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator

from server.exceptions import Error, NotFound, WrongArguments, WrongFormat
from . import models


class LoginRequired(Error):
    code = 'login_required'
    message = '请先登录'


class PermissionRequired(Error):
    code = 'permission_required'
    message = '权限不足'


class ProfileRequired(Error):
    code = 'profile_required'
    message = '请完善个人信息'


def group_validator(group):
    if group not in User.groups:
        raise ValidationError('用户组不存在')


class User:
    json_fields = ('pk', 'is_staff', 'group', 'profile_ok',
                   'display_name', 'nickname', 'name', 'sno', 'tel',
                   'email', 'gender', 'qq', 'school', 'grade', 'token',
                   'token_short')
    update_fields = ('group', 'nickname', 'name', 'sno', 'tel', 'email',
                     'gender', 'qq', 'school', 'grade')
    groups = {
        'staff': '管理员',
        'ustc': '中国科学技术大学',
        'other': '其他选手',
        'banned': '已封禁',
    }
    profile_required = {
        'staff': ['nickname'],
        'ustc': ['nickname', 'name', 'sno', 'tel', 'email', 'gender'],
        'other': ['nickname'],
        'banned': ['nickname'],
    }
    no_board_groups = ['staff', 'other', 'banned']
    no_score_groups = ['staff', 'banned']
    subscribers = []
    _validators = {
        'group': group_validator,
        'nickname': RegexValidator(r'^.{1,30}$', '昵称应为 1～30 个字符'),
        'name': RegexValidator(r'^.{2,30}$', '姓名应为 2～30 个字符'),
        'sno': RegexValidator(r'^[a-zA-Z0-9]{4,30}$', '学号格式错误'),
        'tel': RegexValidator(r'^.{5,20}$', '电话格式错误'),
        'email': EmailValidator('邮箱格式错误'),
        'gender': RegexValidator(r'^(female|male|other)$',
                                 '性别应为 female，male，other 之一'),
        # QQ 号码可能是邮箱的形式，或许还有别的形式，所以用比较宽松的规则
        'qq': RegexValidator(r'^.{5,50}$', 'QQ 号码格式错误'),
        'school': RegexValidator(r'^.{1,30}$', '学院格式错误'),
        'grade': RegexValidator(r'^.{1,10}$', '年级格式错误'),
    }
    _private_key = OpenSSL.crypto.load_privatekey(
        OpenSSL.crypto.FILETYPE_PEM, settings.PRIVATE_KEY)

    def __init__(self, context, obj: models.User):
        self._context = context
        self._obj = obj

    @classmethod
    def test_authenticated(cls, context):
        if context.elevated:
            return
        if not context.user.is_authenticated:
            raise LoginRequired()

    @classmethod
    def test_permission(cls, context, *permissions):
        if context.elevated:
            return
        for permission in permissions:
            if context.user.has_perm(permission):
                return
        raise PermissionRequired()

    @classmethod
    def test_profile(cls, context):
        if context.elevated:
            return
        if not cls.get(context, context.user.pk).profile_ok:
            raise ProfileRequired()

    @classmethod
    def create(cls, context, group, user=None, **kwargs):
        User.test_permission(context)
        context = context.copy(elevated=False)
        if user is None:
            user = get_user_model().objects.create_user(str(uuid4()))
        self = cls(context, models.User(user=user.pk))
        pk = str(user.pk)
        sig = base64.b64encode(OpenSSL.crypto.sign(
            self._private_key, pk.encode(), 'sha256')).decode()
        self._obj.token = pk + ':' + sig
        self._update(group=group, **kwargs)
        new = self._json_all
        for subscriber in self.subscribers:
            subscriber(None, new)
        return self

    @classmethod
    def get(cls, context, pk):
        if pk is None:
            raise WrongArguments()
        try:
            return cls(context, models.User.objects.get(user=pk))
        except models.User.DoesNotExist:
            raise NotFound('用户不存在')

    @classmethod
    def get_all(cls, context):
        return [cls(context, i) for i in models.User.objects.order_by('pk')]

    def update(self, **kwargs):
        if 'group' in kwargs and kwargs['group'] != self.group:
            User.test_permission(self._context, 'user.full')
        if self._context.user.pk != self.pk:
            User.test_permission(self._context, 'user.full')
        old = self._json_all
        self._update(**kwargs)
        new = self._json_all
        for subscriber in self.subscribers:
            subscriber(old, new)

    def _update(self, **kwargs):
        for k, v in kwargs.items():
            if k in {'group', 'nickname', 'name', 'sno', 'tel', 'email',
                     'gender', 'qq', 'school', 'grade'}:
                v = v or None
                try:
                    v is None or self._validators[k](v)
                except ValidationError as e:
                    raise WrongFormat(e.message)
                setattr(self._obj, k, v)
            else:
                raise WrongArguments()
        self._obj.save()
        self._obj.refresh_from_db()

    def delete(self):
        User.test_permission(self._context, 'user.full')
        old = self._json_all
        self.user.delete()
        self._obj.delete()
        self._obj = None
        for subscriber in self.subscribers:
            subscriber(old, None)

    @property
    def json(self):
        result = {}
        for i in self.json_fields:
            try:
                result[i] = getattr(self, i)
            except PermissionRequired:
                pass
        return result

    @property
    def _json_all(self):
        return type(self)(self._context.copy(elevated=True), self._obj).json

    @property
    def profile_ok(self):
        if self.group == 'banned':
            return False
        for field in self.profile_required[self.group]:
            if field.startswith('/'):
                # 这种记法表示 N 选 K
                *fields, minimum = field[1:].split('/')
                count = sum(getattr(self, i) is not None for i in fields)
                if count < int(minimum):
                    return False
            else:
                # 普通的必填字段
                if getattr(self, field) is None:
                    return False
        return True

    @property
    def pk(self):
        return self._obj.user

    @property
    def user(self):
        return get_user_model().objects.get(pk=self.pk)

    @property
    def is_staff(self):
        return self.user.is_staff

    @property
    def group(self):
        return self._obj.group

    @property
    def display_name(self):
        return self.nickname

    @property
    def nickname(self):
        return self._obj.nickname

    @property
    def name(self):
        if self._context.user.pk != self.pk:
            User.test_permission(self._context, 'user.full',
                                 f'user.view_{self.group}')
        return self._obj.name

    @property
    def sno(self):
        if self._context.user.pk != self.pk:
            User.test_permission(self._context, 'user.full',
                                 f'user.view_{self.group}')
        return self._obj.sno

    @property
    def tel(self):
        if self._context.user.pk != self.pk:
            User.test_permission(self._context, 'user.full',
                                 f'user.view_{self.group}')
        return self._obj.tel

    @property
    def email(self):
        if self._context.user.pk != self.pk:
            User.test_permission(self._context, 'user.full',
                                 f'user.view_{self.group}')
        return self._obj.email

    @property
    def gender(self):
        if self._context.user.pk != self.pk:
            User.test_permission(self._context, 'user.full',
                                 f'user.view_{self.group}')
        return self._obj.gender

    @property
    def qq(self):
        if self._context.user.pk != self.pk:
            User.test_permission(self._context, 'user.full',
                                 f'user.view_{self.group}')
        return self._obj.qq

    @property
    def school(self):
        if self._context.user.pk != self.pk:
            User.test_permission(self._context, 'user.full',
                                 f'user.view_{self.group}')
        return self._obj.school

    @property
    def grade(self):
        if self._context.user.pk != self.pk:
            User.test_permission(self._context, 'user.full',
                                 f'user.view_{self.group}')
        return self._obj.grade

    @property
    def token(self):
        if self._context.user.pk != self.pk:
            User.test_permission(self._context)
        return self._obj.token

    @property
    def token_short(self):
        if self._context.user.pk != self.pk:
            User.test_permission(self._context, 'user.full',
                                 f'user.view_{self.group}')
        token = self._obj.token
        return token[: token.find(':') + 11] + '...'
