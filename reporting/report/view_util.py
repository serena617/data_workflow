"""
    Status monitor utilities to support 'report' views
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from report.models import DataRun, RunStatus, IPTS, Instrument, Error, StatusQueue, Task, InstrumentStatus, WorkflowSummary
from django.core.urlresolvers import reverse
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect
from django.utils import dateformat, timezone
import datetime
from django.conf import settings
import logging
import sys
import json
from django.db import connection, transaction
from django.core.cache import cache

import dasmon.view_util
import reporting_app.view_util

def fill_template_values(request, **template_args):
    """
        Fill the template argument items needed to populate
        side bars and other satellite items on the pages.
        
        Only the arguments common to all pages will be filled.
    """
    if "instrument" not in template_args:
        return template_args
    
    instr = template_args["instrument"].lower()
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instr)

    # Get last experiment and last run
    last_run_id = DataRun.objects.get_last_cached_run(instrument_id)
    if last_run_id is None:
        last_expt_id = IPTS.objects.get_last_ipts(instrument_id)
    else:
        last_expt_id = last_run_id.ipts_id
    template_args['last_expt'] = last_expt_id
    template_args['last_run'] = last_run_id

    # Get base IPTS URL
    base_ipts_url = reverse('report.views.ipts_summary',args=[instr,'0000'])
    base_ipts_url = base_ipts_url.replace('/0000','')
    template_args['base_ipts_url'] = base_ipts_url
    
    # Get base Run URL
    base_run_url = reverse('report.views.detail',args=[instr,'0000'])
    base_run_url = base_run_url.replace('/0000','')
    template_args['base_run_url'] = base_run_url
    
    # Get run rate and error rate
    r_rate, e_rate = retrieve_rates(instrument_id, last_run_id)
    template_args['run_rate'] = str(r_rate)
    template_args['error_rate'] = str(e_rate)
    
    template_args = dasmon.view_util.fill_template_values(request, **template_args)

    return template_args

def needs_reduction(request, run_id):
    """
        Determine whether we need a reduction link to 
        submit a run for automated reduction
        @param request: HTTP request object
        @param run_id: DataRun object
    """
    # Get REDUCTION.DATA_READY queue
    try:
        red_queue = StatusQueue.objects.get(name="REDUCTION.DATA_READY")
    except StatusQueue.DoesNotExist:
        logging.error(sys.exc_value)
        return False

    # Check whether we have a task for this queue    
    tasks = Task.objects.filter(instrument_id=run_id.instrument_id,
                                input_queue_id=red_queue)
    if len(tasks)==1 and \
        (tasks[0].task_class is None or len(tasks[0].task_class)==0) \
        and len(tasks[0].task_queue_ids.all())==0:
            return False
       
    return True
    
def send_processing_request(instrument_id, run_id, user=None, destination=None):
    """
        Send an AMQ message to the workflow manager to reprocess
        the run
        @param instrument_id: Instrument object
        @param run_id: DataRun object
    """
    if destination is None:
        destination = '/queue/POSTPROCESS.DATA_READY'
    # Build up dictionary
    data_dict = {'facility': 'SNS',
                 'instrument': str(instrument_id),
                 'ipts': run_id.ipts_id.expt_name.upper(),
                 'run_number': run_id.run_number,
                 'data_file': run_id.file
                 }
    if user is not None:
        data_dict['information'] = "Requested by %s" % user

    data = json.dumps(data_dict)
    reporting_app.view_util.send_activemq_message(destination, data)
    logging.info("Reduction requested: %s" % str(data))
    
def processing_request(request, instrument, run_id, destination):
    """
        Process a request for post-processing
        @param instrument: instrument name
        @param run_id: run number [string]
        @param destination: outgoing AMQ queue
    """
    # Get instrument
    instrument_id = get_object_or_404(Instrument, name=instrument.lower())
    run_object = get_object_or_404(DataRun, instrument_id=instrument_id,run_number=run_id)
    try:
        send_processing_request(instrument_id, run_object, request.user,
                                          destination=destination)
    except:
        logging.error("Could not send post-processing request: %s" % destination)
        logging.error(sys.exc_value)
        return HttpResponseServerError()
    return redirect(reverse('report.views.detail',args=[instrument, run_id]))
    
def retrieve_rates(instrument_id, last_run_id):
    """
        Retrieve the run rate and error rate for an instrument.
        Try to get it from the cache if possible.
        @param instrument_id: Instrument object
        @param last_run_id: DataRun object
    """
    last_run = None
    if last_run_id is not None:
        last_run = last_run_id.run_number
        
    # Check whether we have a cached value and whether it is up to date
    last_cached_run = cache.get('%s_rate_last_run' % instrument_id.name)
    
    def _get_rate(id_name):
        rate = cache.get('%s_%s_rate' % (instrument_id.name, id_name))
        if rate is not None and last_cached_run is not None and last_run==last_cached_run:
            return cache.get('%s_%s_rate' % (instrument_id.name, id_name))
        return None
    
    runs = _get_rate('run')
    errors = _get_rate('error')
    
    # If we didn't find good rates in the cache, recalculate them
    if runs is None or errors is None:
        runs = run_rate(instrument_id)
        errors = error_rate(instrument_id)
        cache.set('%s_run_rate' % instrument_id.name, runs, settings.RUN_RATE_CACHE_TIMEOUT)
        cache.set('%s_error_rate' % instrument_id.name, errors, settings.RUN_RATE_CACHE_TIMEOUT)
        cache.set('%s_rate_last_run' % instrument_id.name, last_run)
        
    return runs, errors
    
@transaction.commit_on_success
def run_rate(instrument_id, n_hours=24):
    """
        Returns the rate of new runs for the last n_hours hours.
        @param instrument_id: Instrument model object
        @param n_hours: number of hours to track
    """
    # Try calling the stored procedure (faster)
    try:
        cursor = connection.cursor()
        cursor.callproc("run_rate", (instrument_id.id,))
        msg = cursor.fetchone()[0]
        cursor.execute('FETCH ALL IN "%s"' % msg)
        rows = cursor.fetchall()
        cursor.close()
        return [ [int(r[0]), int(r[1])] for r in rows ]
    except:
        connection.close()
        logging.error("Run rate (%s): %s" % (str(instrument_id), sys.exc_value))
        
        # Do it by hand (slow)
        time = timezone.now()
        runs=[]
        running_sum = 0
        for i in range(n_hours):
            t_i = time-datetime.timedelta(hours=i+1)
            n = DataRun.objects.filter(instrument_id=instrument_id, created_on__gte=t_i).count()
            n -= running_sum
            running_sum += n
            runs.append([-i,n])
        return runs

@transaction.commit_on_success
def error_rate(instrument_id, n_hours=24):
    """
        Returns the rate of errors for the last n_hours hours.
        @param instrument_id: Instrument model object
        @param n_hours: number of hours to track
    """
    # Try calling the stored procedure (faster)
    try:
        cursor = connection.cursor()
        cursor.callproc("error_rate", (instrument_id.id,))
        msg = cursor.fetchone()[0]
        cursor.execute('FETCH ALL IN "%s"' % msg)
        rows = cursor.fetchall()
        cursor.close()
        return [ [int(r[0]), int(r[1])] for r in rows ]
    except:
        connection.close()
        logging.error("Error rate (%s): %s" % (str(instrument_id), sys.exc_value))
        
        # Do it by hand (slow)
        time = timezone.now()
        errors=[]
        running_sum = 0
        for i in range(n_hours):
            t_i = time-datetime.timedelta(hours=i+1)
            n = Error.objects.filter(run_status_id__run_id__instrument_id=instrument_id, run_status_id__created_on__gte=t_i).count()
            n -= running_sum
            running_sum += n
            errors.append([-i,n])
        return errors
        
def get_current_status(instrument_id):
    """
        Get current status information such as the last
        experiment/run for a given instrument.
        
        Used to populate AJAX response, so must not contain Model objects
        
        @param instrument_id: Instrument model object
    """
    # Get last experiment and last run
    last_run_id = DataRun.objects.get_last_cached_run(instrument_id)
    if last_run_id is None:
        last_expt_id = IPTS.objects.get_last_ipts(instrument_id)
    else:
        last_expt_id = last_run_id.ipts_id

    r_rate, e_rate = retrieve_rates(instrument_id, last_run_id)
    data_dict = {
                 'run_rate':r_rate,
                 'error_rate':e_rate,
                 }
    
    if last_run_id is not None:
        localtime = timezone.localtime(last_run_id.created_on)
        df = dateformat.DateFormat(localtime)
        data_dict['last_run_id']=last_run_id.id
        data_dict['last_run']=last_run_id.run_number
        data_dict['last_run_time']=df.format(settings.DATETIME_FORMAT)
    
    if last_expt_id is not None:
        data_dict['last_expt_id']=last_expt_id.id
        data_dict['last_expt']=last_expt_id.expt_name.upper()

    return data_dict

def get_post_processing_status(red_timeout=0.25, yellow_timeout=10):
    """
        Get the health status of post-processing services
        @param red_timeout: number of hours before declaring a process dead
        @param yellow_timeout: number of seconds before declaring a process slow
    """
    status_dict = {}
    delta_short = datetime.timedelta(seconds=yellow_timeout)
    delta_long = datetime.timedelta(hours=red_timeout)
 
    try:
        run_ids = InstrumentStatus.objects.all().values_list('last_run_id')
        latest_run = RunStatus.objects.filter(run_id__in=run_ids,
                                              queue_id__name='POSTPROCESS.DATA_READY').latest('created_on')
        
        # If we didn't get a CATALOG.STARTED message within a few seconds, 
        # the cataloging agent has a problem
        try:
            latest_catalog_start = RunStatus.objects.filter(queue_id__name='CATALOG.STARTED',
                                                            run_id=latest_run.run_id).latest('created_on')
            time_catalog_start = latest_catalog_start.created_on
        except:
            time_catalog_start = timezone.now()
                
        if time_catalog_start-latest_run.created_on>delta_long:
            status_dict["catalog"]=2
        elif time_catalog_start-latest_run.created_on>delta_short:
            status_dict["catalog"]=1
        else:
            status_dict["catalog"]=0

        # If we didn't get a REDUCTION.STARTED message within a few seconds, 
        # the cataloging agent has a problem
        try:
            latest_reduction_ready = RunStatus.objects.filter(queue_id__name='REDUCTION.DATA_READY',
                                                              run_id=latest_run.run_id).latest('created_on')
            time_reduction_ready = latest_reduction_ready.created_on
        except:
            time_reduction_ready = timezone.now()
        try:
            latest_reduction_start = RunStatus.objects.filter(queue_id__name='REDUCTION.STARTED',
                                                              run_id=latest_run.run_id).latest('created_on')
            time_reduction_start = latest_reduction_start.created_on
        except:
            time_reduction_start = timezone.now()
                
        if time_reduction_start-time_reduction_ready>delta_long:
            status_dict["reduction"]=2
        elif time_reduction_start-time_reduction_ready>delta_short:
            status_dict["reduction"]=1
        else:
            status_dict["reduction"]=0
    except:
        logging.error("Could not determine post-processing status")
        logging.error(sys.exc_value)
    
    return status_dict
    
def get_run_status_text(run_id, show_error=False, use_element_id=False):
    """
        Get a textual description of the current status
        for a given run
        @param run_id: run object
        @param show_error: if true, the last error will be whow, otherwise "error"
    """
    status = 'unknown'
    try:
        if use_element_id:
            element_id = "id='run_id_%s'" % run_id.id
        else:
            element_id = ''
        s = WorkflowSummary.objects.get(run_id=run_id)
        if s.complete is True:
            status = "<span %s class='green'>complete</span>" % element_id
        else:
            last_error = run_id.last_error()
            if last_error is not None:
                if show_error:
                    status = "<span %s class='red'>%s</span>" % (element_id, last_error)
                else:
                    status = "<span %s class='red'><b>error</b></span>" % element_id
            else:
                status = "<span %s class='red'>incomplete</span>" % element_id
    except:
        logging.error("report.view_util.get_run_status_text: %s" % sys.exc_value)
    return status

def get_run_list_dict(run_list):
    """
        Get a list of run object and transform it into a list of
        dictionaries that can be used to fill a table.
        
        @param run_list: list of run object (usually a QuerySet)
    """
    run_dicts = []
    try:
        for r in run_list:
            localtime = timezone.localtime(r.created_on)
            df = dateformat.DateFormat(localtime)
            
            run_url = reverse('report.views.detail', args=[str(r.instrument_id), r.run_number])
            instr_url = reverse('dasmon.views.live_runs', args=[str(r.instrument_id)])
            
            run_dicts.append({"instrument_id": "<a href='%s'>%s</a>" % (instr_url, str(r.instrument_id)),
                             "run": "<a href='%s'>%s</a>" % (run_url, r.run_number),
                             "run_id": str(r.id),
                             "timestamp": str(df.format(settings.DATETIME_FORMAT)),
                             "status": get_run_status_text(r, use_element_id=True)
                             })
    except:
        logging.error("report.view_util.get_run_list_dict: %s" % sys.exc_value)
    return run_dicts