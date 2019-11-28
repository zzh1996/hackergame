from urllib.parse import urlencode
from urllib.request import urlopen
from xml.etree import ElementTree

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path

from .base import BaseLoginView


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
        with urlopen(
            'https://passport.ustc.edu.cn/serviceValidate?' +
            urlencode({'service': self.service, 'ticket': self.ticket})
        ) as req:
            tree = ElementTree.fromstring(req.read())[0]
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
