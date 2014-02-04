# -*- coding: utf-8 -*-
# Copyright (C) 2011-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

name = 'turbogears'
project = u'Interfaces web Vigilo'

pdf_documents = [
    ('auth', "auth-acls", "Authentification et autorisations", u'Vigilo'),
    ('dev', "dev-%s" % name, u"%s : Manuel développeur" % project, u'Vigilo'),
]

latex_documents = [
    ('auth', 'vigilo-auth-acls.tex', u"Authentification et autorisations",
     'AA100004-2/ADM00004', 'vigilo'),
    ('dev', 'dev-%s.tex' % name, u"%s : Manuel développeur" % project,
     'AA100004-2/DEV00015', 'vigilo'),
]

execfile("../buildenv/doc/conf.py")
