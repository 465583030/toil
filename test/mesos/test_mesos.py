import tempfile
from time import sleep
import shutil
import unittest
import os
import sys
from mesos.interface import mesos_pb2
from Queue import Queue
from jobTree.batchSystems.mesos import JobTreeJob, ResourceRequirement
from jobTree.test.mesos.ResumeTest import *
from jobTree.test.mesos.ResumeTest import run as testRun
from jobTree.test.mesos.StressTest import main as stressMain
import subprocess
import threading
from jobTree.test import JobTreeTest


class TestMesos(JobTreeTest):

    class MesosMasterThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.popen = subprocess.Popen("mesos-master --registry=in_memory --ip=127.0.0.1", shell=True)


    class MesosSlaveThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.popen = None

        def run(self):
            self.popen = subprocess.Popen("mesos-slave --ip=127.0.0.1 --master=127.0.0.1:5050", shell=True)

    master=MesosMasterThread()
    slave=MesosSlaveThread()

    @classmethod
    def setUpClass(cls):
        super( TestMesos, cls).setUpClass()
        cls.master.setDaemon(True)
        cls.slave.setDaemon(True)
        cls.master.start()
        cls.slave.start()

    @classmethod
    def tearDownClass(cls):
        super( TestMesos, cls).tearDownClass()
        cls.master.popen.kill()
        cls.slave.popen.kill()

    @classmethod
    def killSlave(cls):
        pid = cls.slave.popen.pid
        os.kill(pid, 9)

    @classmethod
    def startSlave(cls):
        cls.slave.run()

    def setUp(self):
        # subprocess.check_call("rm -rf /tmp/mesos/")
        self.startDir=os.getcwd()
        self.tempDir=tempfile.mkdtemp()
        os.chdir(self.tempDir)

    def tearDown(self):
        os.chdir(self.startDir)
        shutil.rmtree(self.tempDir)

    def test_hello_world(self):
        dir = os.path.abspath(os.path.dirname(__file__))
        subprocess.check_call("python {}/jobTree_HelloWorld.py --batchSystem=mesos --logLevel=DEBUG".format(dir), shell=True)
        self.assertTrue(os.path.isfile("./bar_bam.txt"))

    def test_class_script(self):
        dir = os.path.abspath(os.path.dirname(__file__))
        subprocess.check_call("python {}/LongTest.py --batchSystem=mesos".format(dir), shell=True)
        self.assertTrue(os.path.isfile("./hello_world_child2.txt"))
        self.assertTrue(os.path.isfile("./hello_world_follow.txt"))

    def test_stress(self):
        """
        set task number to number of files you wish to create. Actual number of tasks is tasks+2
        Right now task is set to fail 1/2 tries. To change this, go to badExecutor launchTask method
        """
        tasks=10
        stressMain(tasks=tasks)
        for i in range (0,tasks/2):
            self.assertTrue(os.path.isfile("./hello_world_child{}.txt".format(i)), "actual files: {}".format(os.listdir(".")))
            self.assertTrue(os.path.isfile("./hello_world_follow{}.txt".format(i)),  "actual files: {}".format(os.listdir(".")))

    # def test_resume(self):
    #     mainT = threading.Thread(target=testRun,args=(3,))
    #     mainT.start()
    #     #This isn't killing the slave. we need possibly kill -KILL subprocess call with pid.
    #     print "killing"
    #     TestMesos.killSlave()
    #     print "killed"
    #     TestMesos.startSlave()
    #     mainT.join()
    #     self.assertTrue(os.path.isfile("./hello_world_child2.txt"))
    #     self.assertTrue(os.path.isfile("./hello_world_follow.txt"))

    # Test for mesos only. Problem: mesos is daemonized, doesnt quit by itself.
    # def test_mesos_only(self):
    #     sys.argv[1]="127.0.0.1:5050"
    #     killQueue, updatedJobQueue, queue = Queue(), Queue(), Queue()
    #
    #     job1 = JobTreeJob(jobID=1, memory=1, cpu=1, command="echo 'job1'>>job1.txt",cwd=os.getcwd())
    #     job2 = JobTreeJob(jobID=2, memory=1, cpu=1, command="echo 'job2'>>job2.txt",cwd=os.getcwd())
    #
    #     queue.put(job1)
    #     queue.put(job2)
    #
    #     key = ResourceSummary.ResourceSummary(memory=1, cpu=1)
    #
    #     dictionary = {key:queue}
    #
    #     executor = mesos_pb2.ExecutorInfo()
    #     executor.executor_id.value = "default"
    #     executor.command.value = MesosFrameWorkThread.executorScriptPath()
    #     executor.name = "Test Executor (Python)"
    #     executor.source = "python_test"
    #
    #     framework = mesos_pb2.FrameworkInfo()
    #     framework.user = "" # Have Mesos fill in the current user.
    #     framework.name = "JobTree Framework (Python)"
    #
    #     framework.principal = "test-framework-python"
    #     implicitAcknowledgements=1
    #
    #     runningDictionary={}
    #
    #     driver = MesosSchedulerDriver(
    #                 MesosScheduler(implicitAcknowledgements=implicitAcknowledgements, executor=executor, job_queues=dictionary,
    #                                kill_queue=killQueue,
    #                                running_dictionary=runningDictionary, updated_job_queue=updatedJobQueue),
    #                 framework,
    #                 sys.argv[1],
    #                 implicitAcknowledgements)
    #
    #
    #     driver.run()
    #     sleep(2)
    #
    #     self.assertTrue(os.path.isfile("./job1.txt"))
    #     self.assertTrue(os.path.isfile("./job2.txt"))
    #     driver.stop()