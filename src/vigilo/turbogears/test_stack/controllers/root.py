from vigilo.turbogears.controllers.auth import AuthController
from vigilo.turbogears.controllers.selfmonitoring import SelfMonitoringController
from vigilo.turbogears.controllers.custom import CustomController
from vigilo.turbogears.controllers.error import ErrorController
from vigilo.turbogears.controllers.autocomplete import AutoCompleteController
from vigilo.turbogears.controllers.proxy import ProxyController
from vigilo.turbogears.controllers.api.root import ApiRootController

class RootController(AuthController, SelfMonitoringController):
    error = ErrorController()
    autocomplete = AutoCompleteController()
    nagios = ProxyController('nagios', '/nagios/')
    api = ApiRootController()
    custom = CustomController()
