
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import SimpleItem
from zope.component import getGlobalSiteManager
from zope.component import queryMultiAdapter
from zope.component.hooks import getSite
from zope.interface import implementer
from collective.googleanalytics.config import DIMENSIONS_CHOICES
from collective.googleanalytics.config import METRICS_CHOICES
from collective.googleanalytics.config import VISUALIZATION_CHOICES
from collective.googleanalytics.interfaces.plugins import IAnalyticsPlugin
from collective.googleanalytics.interfaces.report import IAnalyticsReport


@implementer(IAnalyticsReport)
class AnalyticsReport(PropertyManager, SimpleItem):
    """
    A Google Analytics report. The AnalyticsReport object defines all of the parameters
    used to query Google and format the result into a report.
    """

    i18n_domain = 'collective.googleanalytics'

    security = ClassSecurityInfo()

    security.declarePrivate('__init__')
    security.declarePrivate('title')
    security.declarePrivate('description')
    security.declarePrivate('i18n_domain')
    security.declarePrivate('categories')
    security.declarePrivate('plugin_names')
    security.declarePrivate('metrics')
    security.declarePrivate('dimensions')
    security.declarePrivate('filters')
    security.declarePrivate('sort')
    security.declarePrivate('start_date')
    security.declarePrivate('end_date')
    security.declarePrivate('max_results')
    security.declarePrivate('columns')
    security.declarePrivate('row_repeat')
    security.declarePrivate('rows')
    security.declarePrivate('viz_type')
    security.declarePrivate('viz_options')
    security.declarePrivate('body')

    _properties = (
        {'id': 'title', 'type': 'ustring', 'mode': 'w',
         'label': 'Title'},
        {'id': 'description', 'type': 'utext', 'mode': 'w',
         'label': 'Description'},
        {'id': 'i18n_domain', 'type': 'ustring', 'mode': 'w',
         'label': 'I18n Domain'},
        {'id': 'categories', 'type': 'multiple selection', 'mode': 'w',
         'label': 'Categories', 'select_variable': 'getCategoriesChoices'},
        {'id': 'plugin_names', 'type': 'multiple selection', 'mode': 'w',
         'label': 'Plugins', 'select_variable': 'getPluginNameChoices'},
        {'id': 'metrics', 'type': 'multiple selection', 'mode': 'w',
         'label': 'Query Metrics', 'select_variable': 'getMetricsChoices'},
        {'id': 'dimensions', 'type': 'multiple selection', 'mode': 'w',
         'label': 'Query Dimensions', 'select_variable': 'getDimensionsChoices'},
        {'id': 'filters', 'type': 'ulines', 'mode': 'w',
         'label': 'Query Filters'},
        {'id': 'sort', 'type': 'ulines', 'mode': 'w',
         'label': 'Query Sort'},
        {'id': 'start_date', 'type': 'ustring', 'mode': 'w',
         'label': 'Query Start Date'},
        {'id': 'end_date', 'type': 'ustring', 'mode': 'w',
         'label': 'Query End Date'},
        {'id': 'max_results', 'type': 'ustring', 'mode': 'w',
         'label': 'Query Maximum Results'},
        {'id': 'columns', 'type': 'ustring', 'mode': 'w',
         'label': 'Table Columns Expression'},
        {'id': 'row_repeat', 'type': 'ustring', 'mode': 'w',
         'label': 'Table Row Repeat Expression'},
        {'id': 'rows', 'type': 'ustring', 'mode': 'w',
         'label': 'Table Rows Expression'},
        {'id': 'viz_type', 'type': 'selection', 'mode': 'w',
         'label': 'Visualization Type', 'select_variable': 'getVisualizationChoices'},
        {'id': 'viz_options', 'type': 'ulines', 'mode': 'w',
         'label': 'Visualization Options'},
        {'id': 'body', 'type': 'utext', 'mode': 'w',
         'label': 'Report Body'},
    )

    manage_options = (
        PropertyManager.manage_options + SimpleItem.manage_options
    )

    def __init__(self, id, **kwargs):
        self.id = id
        self.title = kwargs.get('title', '')
        self.description = kwargs.get('description', '')
        self.i18n_domain = kwargs.get('i18n_domain', 'collective.googleanalytics')
        self.categories = kwargs.get('categories', [])
        self.plugin_names = kwargs.get('plugin_names', [])
        self.metrics = kwargs.get('metrics', [])
        self.dimensions = kwargs.get('dimensions', [])
        self.filters = kwargs.get('filters', [])
        self.sort = kwargs.get('sort', [])
        self.start_date = kwargs.get('start_date', '')
        self.end_date = kwargs.get('end_date', '')
        self.max_results = kwargs.get('max_results', 'python:1000')
        self.columns = kwargs.get('columns', '')
        self.row_repeat = kwargs.get('row_repeat', '')
        self.rows = kwargs.get('rows', '')
        self.viz_type = kwargs.get('viz_type', 'None')
        self.viz_options = kwargs.get('viz_options', [])
        self.body = kwargs.get('body', '')

    security.declarePrivate('getMetricsChoices')

    def getMetricsChoices(self):
        """
        Return the list of possible metrics.
        """

        choices = list(METRICS_CHOICES)
        for plugin in self.getPlugins(self, self.REQUEST):
            plugin.processMetricsChoices(choices)
        return choices

    security.declarePrivate('getDimensionsChoices')

    def getDimensionsChoices(self):
        """
        Return the list of possible dimensions.
        """

        choices = list(DIMENSIONS_CHOICES)
        for plugin in self.getPlugins(self, self.REQUEST):
            plugin.processDimensionsChoices(choices)
        return choices

    security.declarePrivate('getVisualizationChoices')

    def getVisualizationChoices(self):
        """
        Return the list of visualization types.
        """

        choices = list(VISUALIZATION_CHOICES)
        for plugin in self.getPlugins(self, self.REQUEST):
            plugin.processVisualizationChoices(choices)
        return choices

    security.declarePrivate('getPlugins')

    def getPlugins(self, context, request):
        """
        Returns the plugin adapters for this report.
        """

        results = []
        for plugin_name in self.plugin_names:
            plugin = queryMultiAdapter(
                (context, request, self),
                interface=IAnalyticsPlugin,
                name=plugin_name,
                default=None,
            )
            if plugin:
                results.append(plugin)
        return results

    security.declarePrivate('getPluginNameChoices')

    def getPluginNameChoices(self):
        """
        Return the list of plugin names.
        """

        gsm = getGlobalSiteManager()
        global_plugins = set([p.name for p in gsm.registeredAdapters()
                              if p.provided == IAnalyticsPlugin])

        lsm = getSite().getSiteManager()
        local_plugins = set([p.name for p in lsm.registeredAdapters()
                             if p.provided == IAnalyticsPlugin])

        return sorted(list(global_plugins | local_plugins))


InitializeClass(AnalyticsReport)
