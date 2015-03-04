from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'report.views.summary', name='summary'),
    url(r'^(?P<instrument>[\w]+)/$', 'report.views.instrument_summary'),
    url(r'^(?P<instrument>[\w]+)/update/$', 'report.views.get_instrument_update'),
    url(r'^(?P<instrument>[\w]+)/(?P<run_id>\d+)/$', 'report.views.detail', name='report_detail'),
    url(r'^(?P<instrument>[\w]+)/(?P<run_id>\d+)/reduce/$', 'report.views.submit_for_reduction'),
    url(r'^(?P<instrument>[\w]+)/(?P<run_id>\d+)/catalog/$', 'report.views.submit_for_cataloging'),
    url(r'^(?P<instrument>[\w]+)/(?P<run_id>\d+)/postprocess/$', 'report.views.submit_for_post_processing'),
    url(r'^(?P<instrument>[\w]+)/experiment/(?P<ipts>[\w\-\.]+)/update/$', 'report.views.get_experiment_update'),
    url(r'^(?P<instrument>[\w]+)/experiment/(?P<ipts>[\w\-\.]+)/$', 'report.views.ipts_summary'),
    
    url(r'^(?P<instrument>[\w]+)/errors/$', 'report.views.live_errors'),
    url(r'^(?P<instrument>[\w]+)/errors/update$', 'report.views.get_error_update'),
)
