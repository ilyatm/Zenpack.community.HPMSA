from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import getPage
from pprint import pprint

from datetime import datetime
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import (
    PythonDataSourcePlugin,
    )
from ZenPacks.community.HPMSA.xmltricks import (
    get_health_status,
    parsexml,
    )
from ZenPacks.community.HPMSA.schemas import (
    device_map,
    )
from Products.DataCollector.plugins.DataMaps import ObjectMap
from ZenPacks.community.HPMSA.msaauth import authMsa
import logging

LOG = logging.getLogger('zen.HPMSA')


class Conditions(PythonDataSourcePlugin):

    @classmethod
    def config_key(cls, datasource, context):
        return (
            context.device().id,
            datasource.getCycleTime(context),
            'hpmsa-health',
            )

    @classmethod
    def params(cls, datasource, context):
        return {
            'user': context.zHPMSAUser,
            'password': context.zHPMSAPassword,
            'controllers': context.zHPMSAControllers,
            'secure': context.zHPMSASecureConnection,
            'title': context.title,
            }

    @inlineCallbacks
    def collect(self, config):

        user = config.datasources[0].params['user']
        password = config.datasources[0].params['password']
        controllers = config.datasources[0].params['controllers']
        secure = config.datasources[0].params['secure']
        protocol = 'https' if secure else 'http'

        ip, sessionkey = authMsa(controllers, protocol, user, password, LOG)

        data = self.new_data()
        if ip is None:
            LOG.error('%s: Can\'t authenticate, check settings...', config)
            data['events'].append({
                'device': config.id,
                'severity': 'Critical',
                'eventKey': 'hpmsa-alert',
                'eventClassKey': 'hpmsa-alert',
                'summary': 'Can not connect',
                'message': 'Can not authenticate, check settings...',
                })
            returnValue(None)
        else:
            for component in device_map.keys():
                cmd = device_map[component]['xml_obj_command']
                xml = yield getPage(
                    '{0}://{1}/api/show/{2}'
                    .format(protocol, ip, cmd),
                    headers={"sessionKey": '{0}'.format(sessionkey)}
                    )
                print component
                pprint(parsexml(xml, component))
            # for datasource in config.datasources:

        returnValue(None)
