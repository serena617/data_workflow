from django.db import models
import json

class InstrumentManager(models.Manager):
    def find_instrument(self, instrument):
        """
            Get the object associated to an instrument name
        """
        instrument_ids = super(InstrumentManager, self).get_query_set().filter(name=instrument.lower())
        if len(instrument_ids) > 0:
            return instrument_ids[0]
        return None
    
    def sql_dump(self):
        sql = ''
        instrument_ids = super(InstrumentManager, self).get_query_set()
        max_instr_id = 1
        for item in instrument_ids:
            max_instr_id = max(max_instr_id, item.id)
            sql += 'INSERT INTO report_instrument('
            sql += 'id, name) '
            sql += 'VALUES (%d, ' % item.id
            sql += '\'%s\');\n' % item.name

        sql += "SELECT pg_catalog.setval('report_instrument_id_seq', %d, true);\n" % max_instr_id

        return sql
        

class Instrument(models.Model):
    name = models.CharField(max_length=20, unique=True)
    objects = InstrumentManager()
    def __unicode__(self):
        return self.name
    
    def number_of_runs(self):
        """
            Returns the total number of runs for this instrument
        """
        return DataRun.objects.filter(instrument_id=self).count()
    
    def number_of_expts(self):
        """
            Returns the total number of experiments for this instrument
        """
        return IPTS.objects.filter(instruments=self).count()
    
class IPTSManager(models.Manager):
    
    def ipts_for_instrument(self, instrument_id):
        return super(IPTSManager, self).get_query_set().filter(instruments=instrument_id)
        
    def get_last_ipts(self, instrument_id):
        """
            Get the last experiment object for a given instrument.
            Returns None if nothing was found.
            @param instrument_id: Instrument object 
        """
        ipts_query = super(IPTSManager, self).get_query_set().filter(instruments=instrument_id).order_by('created_on').reverse()
        if len(ipts_query)>0:
            return ipts_query[0]
        return None

class IPTS(models.Model):
    """
        Table holding IPTS information
    """
    expt_name = models.CharField(max_length=20, unique=True)
    instruments = models.ManyToManyField(Instrument, related_name='_ipts_instruments+')
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)
    objects = IPTSManager()
    
    def __unicode__(self):
        return self.expt_name
    
    def number_of_runs(self, instrument_id=None):
        """
            Returns the total number of runs for this IPTS
            on the given instrument.
            @param instrument_id: Instrument object
        """
        if instrument_id is None:
            return DataRun.objects.filter(ipts_id=self).distinct().count()
        return DataRun.objects.filter(ipts_id=self, instrument_id=instrument_id).distinct().count()

class DataRunManager(models.Manager):
    
    def get_last_run(self, instrument_id, ipts_id=None):
        """
            Get the last run for a given instrument and experiment.
            Returns None if nothing was found.
            @param instrument_id: Instrument object
            @param ipts_id: IPTS object
        """
        if ipts_id is None:
            last_run_query = super(DataRunManager, self).get_query_set().filter(instrument_id=instrument_id).order_by('created_on').reverse()
        else:
            last_run_query = super(DataRunManager, self).get_query_set().filter(instrument_id=instrument_id,
                                                                                ipts_id=ipts_id).order_by('created_on').reverse()
        if len(last_run_query)>0:
            return last_run_query[0]
        return None
    
class DataRun(models.Model):
    """
        TODO: run number should be unique for a given instrument
    """
    run_number = models.IntegerField()
    ipts_id = models.ForeignKey(IPTS)
    instrument_id = models.ForeignKey(Instrument)
    file = models.CharField(max_length=128)
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)
    objects = DataRunManager()

    def __unicode__(self):
        return "%s_%d" % (self.instrument_id, self.run_number)
    
    def last_error(self):
        try:
            s = WorkflowSummary.objects.get(run_id=self)
            if s.complete is True:
                return "<span class='green'>complete</span>"
        except:
            # No entry for this run
            pass
        
        errors = Error.objects.filter(run_status_id__run_id=self)#.order_by('-run_status_id__created_on')        
        if len(errors)>0:
            return errors[len(errors)-1].description
        return "<span class='red'>incomplete</span>"

    def json_encode(self):
        """
            Encode the object as a JSON dictionnary
        """
        return json.dumps({"instrument": self.instrument_id.name,
                           "ipts": str(self.ipts_id),
                           "run_number": self.run_number,
                           "data_file": self.file})
    
class StatusQueue(models.Model):
    """
        Table containing the ActiveMQ queue names
        used as status
    """
    name = models.CharField(max_length=100, unique=True)
    is_workflow_input = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.name
    
    
class RunStatusManager(models.Manager):
    
    def status(self, run_id, status_description):
        """
            Returns all database entries for a given run and a given
            status message.
            @param run_id: DataRun object
            @param status_description: status message, as a string
        """
        status_ids = StatusQueue.objects.filter(name__startswith=status_description)
        if len(status_ids)>0:
            status_id = status_ids[0]
            return super(RunStatusManager, self).get_query_set().filter(run_id=run_id, queue_id=status_id)
        return []

    def last_timestamp(self, run_id):
        """
            Returns the last timestamp for this run
            @param run_id: DataRun object
        """
        timestamps = super(RunStatusManager, self).get_query_set().filter(run_id=run_id).order_by('-created_on')
        if len(timestamps)>0:
            return timestamps[0].created_on
        return None
    
    def get_last_error(self, run_id):
        errors = super(RunStatusManager, self).get_query_set().filter(run_id=run_id).order_by('-created_on')
        for item in errors:
            if item.has_errors():
                return item.last_error()
        return None
    
class RunStatus(models.Model):
    """
        Map ActiveMQ messages, which have a header like this:
        headers: {'expires': '0', 'timestamp': '1344613053723', 
                  'destination': '/queue/POSTPROCESS.DATA_READY', 
                  'persistent': 'true', 'priority': '5', 
                  'message-id': 'ID:mac83086.ornl.gov-59780-1344536680877-8:2:1:1:1'}
    """
    ## DataRun this run status belongs to
    run_id = models.ForeignKey(DataRun)
    ## Long name for this status
    queue_id = models.ForeignKey(StatusQueue)
    ## ActiveMQ message ID
    message_id = models.CharField(max_length=100, null=True)
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)
    
    objects = RunStatusManager()
    
    def __unicode__(self):
        return "%s: %s" % (str(self.run_id), str(self.queue_id))
    
    def last_info(self):
        """
            Return the last available information object for this status
        """
        info_list = Information.objects.filter(run_status_id=self)
        if len(info_list)>0:
            return info_list[0]
        return None
    
    def last_error(self):
        """
            Return the last available error object for this status
        """
        error_list = Error.objects.filter(run_status_id=self)
        if len(error_list)>0:
            return error_list[0]
        return None
    
    def has_errors(self):
        return Error.objects.filter(run_status_id=self).count()>0
    
class WorkflowSummaryManager(models.Manager):
    
    def incomplete(self):
        """
            Returns the query set of all incomplete runs
        """
        return super(WorkflowSummaryManager, self).get_query_set().filter(complete=False)
    
    def get_summary(self, run_id):
        """
            Get the run summary for a given DataRun object
            @param run_id: DataRun object
        """
        run_list = super(WorkflowSummaryManager, self).get_query_set().filter(run_id=run_id)
        if len(run_list)>0:
            return run_list[0]
        return None
        
class WorkflowSummary(models.Model):
    """
        Overall status of the workflow for a given run
    """
    run_id = models.ForeignKey(DataRun, unique=True)

    # Overall status of the workflow for this run
    complete = models.BooleanField(default=False)
    
    # Cataloging status
    catalog_started = models.BooleanField(default=False)
    cataloged = models.BooleanField(default=False)
    
    # Automated reduction status
    reduction_needed = models.BooleanField(default=True)
    reduction_started = models.BooleanField(default=False)
    reduced = models.BooleanField(default=False)
    reduction_cataloged = models.BooleanField(default=False)
    reduction_catalog_started = models.BooleanField(default=False)
    
    objects = WorkflowSummaryManager()
    
    def __unicode__(self):
        if self.complete is True:
            return "%s: complete" % str(self.run_id)
        else:
            return str(self.run_id)
    
    def update(self):
        """
            Update status according the messages received
        """
        # Check whether we have data
        if len(RunStatus.objects.status(self.run_id, 'POSTPROCESS.DATA_READY'))==0:
            self.complete = True
            self.save()
            return
            
        # Look for cataloging status
        if len(RunStatus.objects.status(self.run_id, 'CATALOG.COMPLETE'))>0:
            self.cataloged = True
        if len(RunStatus.objects.status(self.run_id, 'CATALOG.STARTED'))>0:
            self.catalog_started = True
            
        # Check whether we need reduction (default is no)
        if len(RunStatus.objects.status(self.run_id, 'REDUCTION.NOT_NEEDED'))>0:
            self.reduction_needed = False
        
        # Look for reduction status
        if len(RunStatus.objects.status(self.run_id, 'REDUCTION.COMPLETE'))>0:
            self.reduced = True
        if len(RunStatus.objects.status(self.run_id, 'REDUCTION.STARTED'))>0:
            self.reduction_started = True
        
        # Look for status of reduced data cataloging
        if len(RunStatus.objects.status(self.run_id, 'REDUCTION_CATALOG.COMPLETE'))>0:
            self.reduction_cataloged = True
        if len(RunStatus.objects.status(self.run_id, 'REDUCTION_CATALOG.STARTED'))>0:
            self.reduction_catalog_started = True
            
        # Determine overall status
        if self.cataloged is True:
            if self.reduction_needed is False or \
               (self.reduced is True and self.reduction_cataloged is True):
                self.complete = True
                
        self.save()

         
class Error(models.Model):
    """
        Details of a particular error event
    """   
    run_status_id = models.ForeignKey(RunStatus)
    description = models.CharField(max_length=200, null=True)
            

class Information(models.Model):
    """
        Extra information associated with a status update
    """
    run_status_id = models.ForeignKey(RunStatus)
    description = models.CharField(max_length=200, null=True)


class TaskManager(models.Manager):
    def sql_dump(self):
        """
            Get the object associated to an instrument name
        """
        task_ids = super(TaskManager, self).get_query_set()
        sql = ''
        max_task_id = 1
        for item in task_ids:
            max_task_id = max(max_task_id, item.id)
            sql += 'INSERT INTO report_task('
            sql += 'id, instrument_id_id, input_queue_id_id, task_class) '
            sql += 'VALUES (%d, ' % item.id
            sql += '%d, ' % item.instrument_id.id
            sql += '%d, ' % item.input_queue_id.id
            sql += '\'%s\');\n' % item.task_class

            for q in item.task_queue_ids.all():
                sql += 'INSERT INTO report_task_task_queue_ids('
                sql += 'task_id, statusqueue_id) '
                sql += 'VALUES (%d, ' % item.id
                sql += '%d);\n' % q.id

            for q in item.success_queue_ids.all():
                sql += 'INSERT INTO report_task_success_queue_ids('
                sql += 'task_id, statusqueue_id) '
                sql += 'VALUES (%d, ' % item.id
                sql += '%d);\n' % q.id
                
        sql += "SELECT pg_catalog.setval('report_task_id_seq', %d, true);\n" % max_task_id

        return sql

class Task(models.Model):
    """
        Define a task
    """
    ## Instrument ID
    instrument_id = models.ForeignKey(Instrument)
    ## Message queue that starts this task
    input_queue_id = models.ForeignKey(StatusQueue)
    ## Python class to be instantiated and run
    task_class = models.CharField(max_length=50, null=True)
    ## Output messages to be sent
    task_queue_ids = models.ManyToManyField(StatusQueue, related_name='_task_task_queue_ids+')
    ## Expected success messages from tasks
    # Map one-to-one with task queue IDs
    success_queue_ids = models.ManyToManyField(StatusQueue, related_name='_task_success_queue_ids+') 
    objects = TaskManager()
    
    def task_queues(self):
        queues = ""
        for q in self.task_queue_ids.all():
            queues += "%s; " % str(q)
        return queues

    def success_queues(self):
        queues = ""
        for q in self.success_queue_ids.all():
            queues += "%s; " % str(q)
        return queues

    def json_encode(self):
        """
            Encode the object as a JSON dictionary
        """
        return json.dumps({"instrument": self.instrument_id.name,
                           "input_queue": str(self.input_queue_id),
                           "task_class": self.task_class,
                           "task_queues": [str(q) for q in self.task_queue_ids.all()],
                           "success_queues": [str(q) for q in self.success_queue_ids.all()]})
        
