from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError
from xml.etree import ElementTree
import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path

from .base import BaseLoginView


logger = logging.getLogger(__name__)


class LoginView(BaseLoginView):
    provider = 'ustc'
    group = 'ustc'
    service: str
    ticket: str
    sno: str

    def get(self, request):
        self.service = request.build_absolute_uri('http://home.ustc.edu.cn/~zzh1996/cas/cas_crypto.html')
        self.ticket = request.GET.get('ticket')
        if not self.ticket:
            return redirect('https://passport.ustc.edu.cn/login?' +
                            urlencode({'service': self.service}))
        if self.check_ticket():
            self.login(sno=self.sno)
        return redirect('hub')

    def check_ticket(self):
        try:
            with urlopen(
                'https://passport.ustc.edu.cn/serviceValidate?' +
                urlencode({'service': self.service, 'ticket': self.ticket}), timeout=15
            ) as req:
                tree = ElementTree.fromstring(req.read())[0]
        except URLError as e:
            messages.error(self.request, '连接统一身份认证平台出错')
            logging.exception(e)
            return False
        cas = '{http://www.yale.edu/tp/cas}'
        if tree.tag != cas + 'authenticationSuccess':
            messages.error(self.request, '登录失败')
            return False
        self.identity = tree.find('attributes').find(cas + 'gid').text.strip()
        self.sno = tree.find(cas + 'user').text.strip()
        return True


urlpatterns = [
    path('ustc/login/', LoginView.as_view()),
]
