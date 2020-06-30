# -*- coding: utf-8 -*-
# Copyright (C) 2006-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Unit and functional test suite for vigiboard."""

from __future__ import print_function
import os
import sys
import unittest
import logging

from tg import config
from paste.deploy import loadapp
from gearbox.main import GearBox
from gearbox.commands.setup_app import SetupAppCommand
from webtest import TestApp

from vigilo.models.session import metadata, DBSession

__all__ = ['setup_db', 'teardown_db', 'TestController']

def setup_db():
    """Method used to build a database"""
    print("Creating model")
    engine = config['tg.app_globals'].sa_engine
    metadata.create_all(engine)

def teardown_db():
    """Method used to destroy a database"""
    print("Destroying model")
    engine = config['tg.app_globals'].sa_engine
    metadata.drop_all(engine)

class SetupApp(SetupAppCommand):
    def _import_module(self, s):
        """
        Import a module.
        """
        # TurboGears/gearbox supposent que l'application
        # ne réside pas dans un sous-module.
        # Cette hypothèse est fausse ici (vigilo.turbogears.test_stack)
        # et on doit rectifier le tir manuellement.
        if s == 'vigilo.websetup':
            from vigilo.turbogears.test_stack import websetup
            return websetup
        return super(SetupApp, self)._import_module(s)


class TestController(unittest.TestCase):
    """
    Base functional test case for the controllers.

    The vigiboard application instance (``self.app``) set up in this test
    case (and descendants) has authentication disabled, so that developers can
    test the protected areas independently of the :mod:`repoze.who` plugins
    used initially. This way, authentication can be tested once and separately.

    Check vigiboard.tests.functional.test_authentication for the repoze.who
    integration tests.

    This is the officially supported way to test protected areas with
    repoze.who-testutil (http://code.gustavonarea.net/repoze.who-testutil/).

    """

    application_under_test = 'main_without_authn'

    def setUp(self):
        """Method called by nose before running each test"""
        # Loading the application:
        conf_dir = '.'
        print("Testing the application using this profile: %s" %
              self.application_under_test)
        wsgiapp = loadapp('config:test.ini#%s' %
            self.application_under_test, relative_to=conf_dir)
        self.app = TestApp(wsgiapp)
        # Setting it up:
        test_file = os.path.join(conf_dir, 'test.ini')
        box = GearBox()
        box.command_manager.add_command('setup-app', SetupApp)
        box.run(['setup-app', '-q', '--debug', '-c', "%s#%s" %
                (test_file, self.application_under_test)])

    def tearDown(self):
        """Method called by nose after running each test"""
        teardown_db()
        del self.app
