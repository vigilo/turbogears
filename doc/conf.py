# -*- coding: utf-8 -*-

project = u'IHMs web'

pdf_documents = [
        ('auth', "auth-acls", "Authentification et autorisations", u'Vigilo'),
]

latex_documents = [
        ('auth', 'vigilo-auth-acls.tex', u"Authentification et autorisations",
         'AA100004-2/ADM00004', 'vigilo'),
]

execfile("../buildenv/doc/conf.py")
