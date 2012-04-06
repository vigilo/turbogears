# -*- coding: utf-8 -*-
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

project = u'IHMs web'

pdf_documents = [
        ('auth', "auth-acls", "Authentification et autorisations", u'Vigilo'),
]

latex_documents = [
        ('auth', 'vigilo-auth-acls.tex', u"Authentification et autorisations",
         'AA100004-2/ADM00004', 'vigilo'),
]

execfile("../buildenv/doc/conf.py")
