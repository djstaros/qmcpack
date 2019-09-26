
import testing
from testing import value_eq,object_eq,failed,TestFailed


machines_data = dict()

def get_machine_data():
    from generic import obj
    from machines import Machine,Workstation,Supercomputer
    if len(machines_data)==0:
        workstations   = obj()
        supercomputers = obj()
        for machine in Machine.machines:
            if isinstance(machine,Workstation):
                workstations.append(machine)
            elif isinstance(machine,Supercomputer):
                supercomputers[machine.name] = machine
            else:
                failed()
            #end if
        #end for
        machines_data['ws'] = workstations
        machines_data['sc'] = supercomputers
    #end if
    ws = machines_data['ws']
    sc = machines_data['sc']
    return ws,sc
#end def get_machine_data



def test_import():
    from machines import Machine,Workstation,InteractiveCluster,Supercomputer
    from machines import Job,job
    from machines import get_machine,get_machine_name
#end def test_import



def test_machine_virtuals():
    from machines import Machine
    arg0 = None
    arg1 = None
    try:
        Machine.query_queue(arg0)
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
    try:
        Machine.submit_jobs(arg0)
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
    try:
        Machine.process_job(arg0,arg1)
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
    try:
        Machine.process_job_options(arg0,arg1)
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
    try:
        Machine.write_job(arg0,arg1,file=False)
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
    try:
        Machine.submit_job(arg0,arg1)
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
#end def test_machine_virtuals



def test_machine_list():
    from machines import Machine

    assert(len(Machine.machines)>0)
    for m in Machine.machines:
        assert(isinstance(m,Machine))
        exists = m.name in Machine.machines
        assert(exists)
        assert(Machine.exists(m.name))
        assert(Machine.is_unique(m))
        m.validate()
    #end for
#end def test_machine_list



def test_machine_add():
    from machines import Machine
    mtest = Machine.machines.first()
    assert(isinstance(mtest,Machine))
    try:
        Machine.add(mtest)
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
    try:
        Machine.add('my_machine')
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
#end def test_machine_add



def test_machine_get():
    from machines import Machine
    mtest = Machine.machines.first()
    assert(isinstance(mtest,Machine))

    m = Machine.get(mtest.name)
    assert(isinstance(m,Machine))
    assert(id(m)==id(mtest))
    try:
        Machine.get(m)
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
    try:
        Machine.get('some_nonexistant_machine')
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
#end def test_machine_get



def test_machine_instantiation():
    from machines import Machine
    # test guards against empty/invalid instantiation
    try:
        Machine()
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
    try:
        Machine(123)
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try
    # test creation of a new machine
    test_name = 'test_machine'
    assert(not Machine.exists(test_name))
    m = Machine(name=test_name)
    assert(isinstance(m,Machine))
    assert(Machine.exists(m.name))
    assert(Machine.is_unique(m))
    m.validate()

    # test guards against multiple instantiation
    try:
        Machine(name=test_name)
        raise TestFailed
    except TestFailed:
        failed()
    except:
        None
    #end try

    # remove test machine
    del Machine.machines.test_machine
    assert(not Machine.exists(test_name))
#end def test_machine_instantiation



def test_machine_process_job():
    from random import randint
    from generic import obj
    from machines import Machine,Job

    nw  = 5
    nwj = 5
    nsj = 5
    nij = 5

    workstations,supercomputers = get_machine_data()

    allow_warn = Machine.allow_warnings
    Machine.allow_warnings = False

    not_idempotent = obj()

    # check workstations
    nworkstations = nw
    if nworkstations is None:
        nworkstations=len(workstations)
    #end if
    nworkstations = min(nworkstations,len(workstations))
    njobs = nwj
    for nm in range(nworkstations):
        if nworkstations<len(workstations):
            machine = workstations.select_random() # select machine at random
        else:
            machine = workstations[nm]
        #end if
        cores_min     = 1
        cores_max     = machine.cores
        processes_min = 1
        processes_max = machine.cores
        threads_min   = 1
        threads_max   = machine.cores
        job_inputs = []
        job_inputs_base = []
        for nj in range(njobs): # vary cores
            cores   = randint(cores_min,cores_max)
            threads = randint(threads_min,threads_max)
            job_inputs_base.append(obj(cores=cores,threads=threads))
        #end for
        for nj in range(njobs): # vary processes
            processes   = randint(processes_min,processes_max)
            threads = randint(threads_min,threads_max)
            job_inputs_base.append(obj(processes=processes,threads=threads))
        #end for
        job_inputs.extend(job_inputs_base)
        for job_input in job_inputs_base: # run in serial
            ji = job_input.copy()
            ji.serial = True
            job_inputs.append(ji)
        #end for
        # perform idempotency test
        machine_idempotent = True
        for job_input in job_inputs:
            job = Job(machine=machine.name,**job_input)
            job2 = obj.copy(job)
            machine.process_job(job2)
            machine_idempotent &= job==job2
        #end for
        if not machine_idempotent:
            not_idempotent[machine.name] = machine
        #end if
    #end for

    # check supercomputers
    njobs = nsj
    small_node_ceiling = 20
    nodes_min   = 1
    cores_min   = 1
    threads_min = 1
    shared_job_inputs = obj(name='some_job',account='some_account')
    for machine in supercomputers:
        job_inputs = []
        job_inputs_base = []
        threads_max = 2*machine.cores_per_node
        # sample small number of nodes more heavily
        nodes_max   = min(small_node_ceiling,machine.nodes)
        cores_max   = min(small_node_ceiling*machine.cores_per_node,machine.cores)
        for nj in range(njobs): # nodes alone
            nodes   = randint(nodes_min,nodes_max)
            threads = randint(threads_min,threads_max)
            job_input = obj(nodes=nodes,threads=threads,**shared_job_inputs)
            job_inputs_base.append(job_input)
        #end for
        for nj in range(njobs): # cores alone
            cores   = randint(cores_min,cores_max)
            threads = randint(threads_min,threads_max)
            job_input = obj(cores=cores,threads=threads,**shared_job_inputs)
            job_inputs_base.append(job_input)
        #end for
        for nj in range(njobs): # nodes and cores
            nodes   = randint(nodes_min,nodes_max)
            cores   = randint(cores_min,cores_max)
            threads = randint(threads_min,threads_max)
            job_input = obj(nodes=nodes,cores=cores,threads=threads,**shared_job_inputs)
            job_inputs_base.append(job_input)
        #end for
        # sample full node set
        nodes_max = machine.nodes
        cores_max = machine.cores
        for nj in range(njobs): # nodes alone
            nodes   = randint(nodes_min,nodes_max)
            threads = randint(threads_min,threads_max)
            job_input = obj(nodes=nodes,threads=threads,**shared_job_inputs)
            job_inputs_base.append(job_input)
        #end for
        for nj in range(njobs): # cores alone
            cores   = randint(cores_min,cores_max)
            threads = randint(threads_min,threads_max)
            job_input = obj(cores=cores,threads=threads,**shared_job_inputs)
            job_inputs_base.append(job_input)
        #end for
        for nj in range(njobs): # nodes and cores
            nodes   = randint(nodes_min,nodes_max)
            cores   = randint(cores_min,cores_max)
            threads = randint(threads_min,threads_max)
            job_input = obj(nodes=nodes,cores=cores,threads=threads,**shared_job_inputs)
            job_inputs_base.append(job_input)
        #end for
        job_inputs.extend(job_inputs_base)
        # now add serial jobs
        for job_input in job_inputs_base:
            ji = job_input.copy()
            ji.serial = True
            job_inputs.append(ji)
        #end for
        # now add local, serial jobs
        for job_input in job_inputs_base:
            ji = job_input.copy()
            ji.serial = True
            ji.local  = True
            job_inputs.append(ji)
        #end for
        # perform idempotency test
        machine_idempotent = True
        for job_input in job_inputs:
            job = Job(machine=machine.name,**job_input)
            job2 = obj.copy(job)
            machine.process_job(job2)
            job_idempotent = object_eq(job,job2)
            if not job_idempotent:
                d,d1,d2 = object_diff(job,job2,full=True)
                change = obj(job_before=obj(d1),job_after=obj(d2))
                msg = machine.name+'\n'+str(change)
                failed(msg)
            #end if
            machine_idempotent &= job_idempotent
        #end for
        if not machine_idempotent:
            not_idempotent[machine.name] = machine
        #end if
    #end for

    if len(not_idempotent)>0:
        mlist = ''
        for name in sorted(not_idempotent.keys()):
            mlist+= '\n  '+name
        #end for
        msg='\n\nsome machines failed process_job idempotency test:{0}'.format(mlist)
        failed(msg)
    #end if
    Machine.allow_warnings = allow_warn

#end def test_machine_process_job



def test_job_run_command():
    from generic import obj
    from machines import Machine,Job

    workstations,supercomputers = get_machine_data()

    allow_warn = Machine.allow_warnings
    Machine.allow_warnings = False

    def parse_job_command(command):
        tokens = command.replace(':',' ').split()
        launcher = tokens[0]
        exe = tokens[-1]
        args = []
        options = obj()
        last_option = None
        for t in tokens[1:-1]:
            if t.startswith('-'):
                options[t] = None
                last_option = t
            elif last_option is not None:
                options[last_option] = t
                last_option = None
            else:
                args.append(t)
            #end if
        #end for
        jc = obj(
            launcher   = launcher,
            executable = exe,
            args       = args,
            options    = options,
            )
        return jc
    #end def parse_job_command

    def job_commands_equal(c1,c2):
        jc1 = parse_job_command(c1)
        jc2 = parse_job_command(c2)
        return object_eq(jc1,jc2)
    #end def job_command_equal

    job_run_ref = obj({
        ('amos'           , 'n1'            ) : 'srun test.x',
        ('amos'           , 'n1_p1'         ) : 'srun test.x',
        ('amos'           , 'n2'            ) : 'srun test.x',
        ('amos'           , 'n2_t2'         ) : 'srun test.x',
        ('amos'           , 'n2_t2_e'       ) : 'srun test.x',
        ('amos'           , 'n2_t2_p2'      ) : 'srun test.x',
        ('bluewaters_xe'  , 'n1'            ) : 'aprun -n 32 test.x',
        ('bluewaters_xe'  , 'n1_p1'         ) : 'aprun -n 1 test.x',
        ('bluewaters_xe'  , 'n2'            ) : 'aprun -n 64 test.x',
        ('bluewaters_xe'  , 'n2_t2'         ) : 'aprun -d 2 -n 32 test.x',
        ('bluewaters_xe'  , 'n2_t2_e'       ) : 'aprun -d 2 -n 32 test.x',
        ('bluewaters_xe'  , 'n2_t2_p2'      ) : 'aprun -d 2 -n 4 test.x',
        ('bluewaters_xk'  , 'n1'            ) : 'aprun -n 16 test.x',
        ('bluewaters_xk'  , 'n1_p1'         ) : 'aprun -n 1 test.x',
        ('bluewaters_xk'  , 'n2'            ) : 'aprun -n 32 test.x',
        ('bluewaters_xk'  , 'n2_t2'         ) : 'aprun -d 2 -n 16 test.x',
        ('bluewaters_xk'  , 'n2_t2_e'       ) : 'aprun -d 2 -n 16 test.x',
        ('bluewaters_xk'  , 'n2_t2_p2'      ) : 'aprun -d 2 -n 4 test.x',
        ('cades'          , 'n1'            ) : 'mpirun -np 36 test.x',
        ('cades'          , 'n1_p1'         ) : 'mpirun -np 1 test.x',
        ('cades'          , 'n2'            ) : 'mpirun -np 72 test.x',
        ('cades'          , 'n2_t2'         ) : 'mpirun -np 36 --npersocket 9 test.x',
        ('cades'          , 'n2_t2_e'       ) : 'mpirun -np 36 --npersocket 9 test.x',
        ('cades'          , 'n2_t2_p2'      ) : 'mpirun -np 4 --npersocket 1 test.x',
        ('cetus'          , 'n1'            ) : 'runjob --np 16 -p 16 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=1 : test.x',
        ('cetus'          , 'n1_p1'         ) : 'runjob --np 1 -p 1 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=1 : test.x',
        ('cetus'          , 'n2'            ) : 'runjob --np 32 -p 16 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=1 : test.x',
        ('cetus'          , 'n2_t2'         ) : 'runjob --np 16 -p 8 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=2 : test.x',
        ('cetus'          , 'n2_t2_e'       ) : 'runjob --np 16 -p 8 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=2 ENV_VAR=1 : test.x',
        ('cetus'          , 'n2_t2_p2'      ) : 'runjob --np 4 -p 2 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=2 : test.x',
        ('chama'          , 'n1'            ) : 'srun test.x',
        ('chama'          , 'n1_p1'         ) : 'srun test.x',
        ('chama'          , 'n2'            ) : 'srun test.x',
        ('chama'          , 'n2_t2'         ) : 'srun test.x',
        ('chama'          , 'n2_t2_e'       ) : 'srun test.x',
        ('chama'          , 'n2_t2_p2'      ) : 'srun test.x',
        ('cooley'         , 'n1'            ) : 'mpirun -np 12 test.x',
        ('cooley'         , 'n1_p1'         ) : 'mpirun -np 1 test.x',
        ('cooley'         , 'n2'            ) : 'mpirun -np 24 test.x',
        ('cooley'         , 'n2_t2'         ) : 'mpirun -np 12 test.x',
        ('cooley'         , 'n2_t2_e'       ) : 'mpirun -np 12 test.x',
        ('cooley'         , 'n2_t2_p2'      ) : 'mpirun -np 4 test.x',
        ('cori'           , 'n1'            ) : 'srun test.x',
        ('cori'           , 'n1_p1'         ) : 'srun test.x',
        ('cori'           , 'n2'            ) : 'srun test.x',
        ('cori'           , 'n2_t2'         ) : 'srun test.x',
        ('cori'           , 'n2_t2_e'       ) : 'srun test.x',
        ('cori'           , 'n2_t2_p2'      ) : 'srun test.x',
        ('edison'         , 'n1'            ) : 'srun test.x',
        ('edison'         , 'n1_p1'         ) : 'srun test.x',
        ('edison'         , 'n2'            ) : 'srun test.x',
        ('edison'         , 'n2_t2'         ) : 'srun test.x',
        ('edison'         , 'n2_t2_e'       ) : 'srun test.x',
        ('edison'         , 'n2_t2_p2'      ) : 'srun test.x',
        ('eos'            , 'n1'            ) : 'aprun -n 16 test.x',
        ('eos'            , 'n1_p1'         ) : 'aprun -n 1 test.x',
        ('eos'            , 'n2'            ) : 'aprun -n 32 test.x',
        ('eos'            , 'n2_t2'         ) : 'aprun -ss -cc numa_node -d 2 -n 16 test.x',
        ('eos'            , 'n2_t2_e'       ) : 'aprun -ss -cc numa_node -d 2 -n 16 test.x',
        ('eos'            , 'n2_t2_p2'      ) : 'aprun -ss -cc numa_node -d 2 -n 4 test.x',
        ('jaguar'         , 'n1'            ) : 'aprun -n 16 test.x',
        ('jaguar'         , 'n1_p1'         ) : 'aprun -n 1 test.x',
        ('jaguar'         , 'n2'            ) : 'aprun -n 32 test.x',
        ('jaguar'         , 'n2_t2'         ) : 'aprun -d 2 -n 16 test.x',
        ('jaguar'         , 'n2_t2_e'       ) : 'aprun -d 2 -n 16 test.x',
        ('jaguar'         , 'n2_t2_p2'      ) : 'aprun -d 2 -n 4 test.x',
        ('komodo'         , 'n1'            ) : 'mpirun -np 12 test.x',
        ('komodo'         , 'n1_p1'         ) : 'mpirun -np 1 test.x',
        ('komodo'         , 'n2'            ) : 'mpirun -np 24 test.x',
        ('komodo'         , 'n2_t2'         ) : 'mpirun -np 12 test.x',
        ('komodo'         , 'n2_t2_e'       ) : 'mpirun -np 12 test.x',
        ('komodo'         , 'n2_t2_p2'      ) : 'mpirun -np 4 test.x',
        ('kraken'         , 'n1'            ) : 'aprun -n 12 test.x',
        ('kraken'         , 'n1_p1'         ) : 'aprun -n 1 test.x',
        ('kraken'         , 'n2'            ) : 'aprun -n 24 test.x',
        ('kraken'         , 'n2_t2'         ) : 'aprun -d 2 -n 12 test.x',
        ('kraken'         , 'n2_t2_e'       ) : 'aprun -d 2 -n 12 test.x',
        ('kraken'         , 'n2_t2_p2'      ) : 'aprun -d 2 -n 4 test.x',
        ('lonestar'       , 'n1'            ) : 'ibrun -n 12 -o 0 test.x',
        ('lonestar'       , 'n1_p1'         ) : 'ibrun -n 1 -o 0 test.x',
        ('lonestar'       , 'n2'            ) : 'ibrun -n 24 -o 0 test.x',
        ('lonestar'       , 'n2_t2'         ) : 'ibrun -n 12 -o 0 test.x',
        ('lonestar'       , 'n2_t2_e'       ) : 'ibrun -n 12 -o 0 test.x',
        ('lonestar'       , 'n2_t2_p2'      ) : 'ibrun -n 4 -o 0 test.x',
        ('matisse'        , 'n1'            ) : 'mpirun -np 16 test.x',
        ('matisse'        , 'n1_p1'         ) : 'mpirun -np 1 test.x',
        ('matisse'        , 'n2'            ) : 'mpirun -np 32 test.x',
        ('matisse'        , 'n2_t2'         ) : 'mpirun -np 16 test.x',
        ('matisse'        , 'n2_t2_e'       ) : 'mpirun -np 16 test.x',
        ('matisse'        , 'n2_t2_p2'      ) : 'mpirun -np 4 test.x',
        ('mira'           , 'n1'            ) : 'runjob --np 16 -p 16 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=1 : test.x',
        ('mira'           , 'n1_p1'         ) : 'runjob --np 1 -p 1 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=1 : test.x',
        ('mira'           , 'n2'            ) : 'runjob --np 32 -p 16 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=1 : test.x',
        ('mira'           , 'n2_t2'         ) : 'runjob --np 16 -p 8 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=2 : test.x',
        ('mira'           , 'n2_t2_e'       ) : 'runjob --np 16 -p 8 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=2 ENV_VAR=1 : test.x',
        ('mira'           , 'n2_t2_p2'      ) : 'runjob --np 4 -p 2 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=2 : test.x',
        ('oic5'           , 'n1'            ) : 'mpirun -np 32 test.x',
        ('oic5'           , 'n1_p1'         ) : 'mpirun -np 1 test.x',
        ('oic5'           , 'n2'            ) : 'mpirun -np 64 test.x',
        ('oic5'           , 'n2_t2'         ) : 'mpirun -np 32 test.x',
        ('oic5'           , 'n2_t2_e'       ) : 'mpirun -np 32 test.x',
        ('oic5'           , 'n2_t2_p2'      ) : 'mpirun -np 4 test.x',
        ('redsky'         , 'n1'            ) : 'srun test.x',
        ('redsky'         , 'n1_p1'         ) : 'srun test.x',
        ('redsky'         , 'n2'            ) : 'srun test.x',
        ('redsky'         , 'n2_t2'         ) : 'srun test.x',
        ('redsky'         , 'n2_t2_e'       ) : 'srun test.x',
        ('redsky'         , 'n2_t2_p2'      ) : 'srun test.x',
        ('serrano'        , 'n1'            ) : 'srun test.x',
        ('serrano'        , 'n1_p1'         ) : 'srun test.x',
        ('serrano'        , 'n2'            ) : 'srun test.x',
        ('serrano'        , 'n2_t2'         ) : 'srun test.x',
        ('serrano'        , 'n2_t2_e'       ) : 'srun test.x',
        ('serrano'        , 'n2_t2_p2'      ) : 'srun test.x',
        ('skybridge'      , 'n1'            ) : 'srun test.x',
        ('skybridge'      , 'n1_p1'         ) : 'srun test.x',
        ('skybridge'      , 'n2'            ) : 'srun test.x',
        ('skybridge'      , 'n2_t2'         ) : 'srun test.x',
        ('skybridge'      , 'n2_t2_e'       ) : 'srun test.x',
        ('skybridge'      , 'n2_t2_p2'      ) : 'srun test.x',
        ('solo'           , 'n1'            ) : 'srun test.x',
        ('solo'           , 'n1_p1'         ) : 'srun test.x',
        ('solo'           , 'n2'            ) : 'srun test.x',
        ('solo'           , 'n2_t2'         ) : 'srun test.x',
        ('solo'           , 'n2_t2_e'       ) : 'srun test.x',
        ('solo'           , 'n2_t2_p2'      ) : 'srun test.x',
        ('stampede2'      , 'n1'            ) : 'ibrun -n 68 -o 0 test.x',
        ('stampede2'      , 'n1_p1'         ) : 'ibrun -n 1 -o 0 test.x',
        ('stampede2'      , 'n2'            ) : 'ibrun -n 136 -o 0 test.x',
        ('stampede2'      , 'n2_t2'         ) : 'ibrun -n 68 -o 0 test.x',
        ('stampede2'      , 'n2_t2_e'       ) : 'ibrun -n 68 -o 0 test.x',
        ('stampede2'      , 'n2_t2_p2'      ) : 'ibrun -n 4 -o 0 test.x',
        ('summit'         , 'n1'            ) : 'jsrun -a 21 -r 2 -b rs -c 21 -d packed -n 2 -g 0 test.x',
        ('summit'         , 'n1_g6'         ) : 'jsrun -a 7 -r 6 -b rs -c 7 -d packed -n 6 -g 1 test.x',
        ('summit'         , 'n2'            ) : 'jsrun -a 21 -r 2 -b rs -c 21 -d packed -n 4 -g 0 test.x',
        ('summit'         , 'n2_g6'         ) : 'jsrun -a 7 -r 6 -b rs -c 7 -d packed -n 12 -g 1 test.x',
        ('summit'         , 'n2_t2'         ) : 'jsrun -a 10 -r 2 -b rs -c 20 -d packed -n 4 -g 0 test.x',
        ('summit'         , 'n2_t2_e'       ) : 'jsrun -a 10 -r 2 -b rs -c 20 -d packed -n 4 -g 0 test.x',
        ('summit'         , 'n2_t2_e_g6'    ) : 'jsrun -a 3 -r 6 -b rs -c 6 -d packed -n 12 -g 1 test.x',
        ('summit'         , 'n2_t2_g6'      ) : 'jsrun -a 3 -r 6 -b rs -c 6 -d packed -n 12 -g 1 test.x',
        ('supermuc'       , 'n1'            ) : 'mpiexec -n 28 test.x',
        ('supermuc'       , 'n1_p1'         ) : 'mpiexec -n 1 test.x',
        ('supermuc'       , 'n2'            ) : 'mpiexec -n 56 test.x',
        ('supermuc'       , 'n2_t2'         ) : 'mpiexec -n 28 test.x',
        ('supermuc'       , 'n2_t2_e'       ) : 'mpiexec -n 28 test.x',
        ('supermuc'       , 'n2_t2_p2'      ) : 'mpiexec -n 4 test.x',
        ('supermucng'     , 'n1'            ) : 'mpiexec -n 48 test.x',
        ('supermucng'     , 'n1_p1'         ) : 'mpiexec -n 1 test.x',
        ('supermucng'     , 'n2'            ) : 'mpiexec -n 96 test.x',
        ('supermucng'     , 'n2_t2'         ) : 'mpiexec -n 48 test.x',
        ('supermucng'     , 'n2_t2_e'       ) : 'mpiexec -n 48 test.x',
        ('supermucng'     , 'n2_t2_p2'      ) : 'mpiexec -n 4 test.x',
        ('taub'           , 'n1'            ) : 'mpirun -np 12 test.x',
        ('taub'           , 'n1_p1'         ) : 'mpirun -np 1 test.x',
        ('taub'           , 'n2'            ) : 'mpirun -np 24 test.x',
        ('taub'           , 'n2_t2'         ) : 'mpirun -np 12 test.x',
        ('taub'           , 'n2_t2_e'       ) : 'mpirun -np 12 test.x',
        ('taub'           , 'n2_t2_p2'      ) : 'mpirun -np 4 test.x',
        ('theta'          , 'n1'            ) : 'aprun -e OMP_NUM_THREADS=1 -d 1 -cc depth -j 1 -n 64 -N 64 test.x',
        ('theta'          , 'n1_p1'         ) : 'aprun -e OMP_NUM_THREADS=1 -d 1 -cc depth -j 1 -n 1 -N 1 test.x',
        ('theta'          , 'n2'            ) : 'aprun -e OMP_NUM_THREADS=1 -d 1 -cc depth -j 1 -n 128 -N 64 test.x',
        ('theta'          , 'n2_t2'         ) : 'aprun -e OMP_NUM_THREADS=2 -d 2 -cc depth -j 1 -n 64 -N 32 test.x',
        ('theta'          , 'n2_t2_e'       ) : 'aprun -e OMP_NUM_THREADS=2 -d 2 -cc depth -j 1 -n 64 -N 32 test.x',
        ('theta'          , 'n2_t2_p2'      ) : 'aprun -e OMP_NUM_THREADS=2 -d 2 -cc depth -j 1 -n 4 -N 2 test.x',
        ('titan'          , 'n1'            ) : 'aprun -n 16 test.x',
        ('titan'          , 'n1_p1'         ) : 'aprun -n 1 test.x',
        ('titan'          , 'n2'            ) : 'aprun -n 32 test.x',
        ('titan'          , 'n2_t2'         ) : 'aprun -d 2 -n 16 test.x',
        ('titan'          , 'n2_t2_e'       ) : 'aprun -d 2 -n 16 test.x',
        ('titan'          , 'n2_t2_p2'      ) : 'aprun -d 2 -n 4 test.x',
        ('tomcat3'        , 'n1'            ) : 'mpirun -np 64 test.x',
        ('tomcat3'        , 'n1_p1'         ) : 'mpirun -np 1 test.x',
        ('tomcat3'        , 'n2'            ) : 'mpirun -np 128 test.x',
        ('tomcat3'        , 'n2_t2'         ) : 'mpirun -np 64 test.x',
        ('tomcat3'        , 'n2_t2_e'       ) : 'mpirun -np 64 test.x',
        ('tomcat3'        , 'n2_t2_p2'      ) : 'mpirun -np 4 test.x',
        ('uno'            , 'n1'            ) : 'srun test.x',
        ('uno'            , 'n1_p1'         ) : 'srun test.x',
        ('uno'            , 'n2'            ) : 'srun test.x',
        ('uno'            , 'n2_t2'         ) : 'srun test.x',
        ('uno'            , 'n2_t2_e'       ) : 'srun test.x',
        ('uno'            , 'n2_t2_p2'      ) : 'srun test.x',
        ('vesta'          , 'n1'            ) : 'runjob --np 16 -p 16 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=1 : test.x',
        ('vesta'          , 'n1_p1'         ) : 'runjob --np 1 -p 1 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=1 : test.x',
        ('vesta'          , 'n2'            ) : 'runjob --np 32 -p 16 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=1 : test.x',
        ('vesta'          , 'n2_t2'         ) : 'runjob --np 16 -p 8 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=2 : test.x',
        ('vesta'          , 'n2_t2_e'       ) : 'runjob --np 16 -p 8 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=2 ENV_VAR=1 : test.x',
        ('vesta'          , 'n2_t2_p2'      ) : 'runjob --np 4 -p 2 $LOCARGS --verbose=INFO --envs OMP_NUM_THREADS=2 : test.x',
        })

    job_inputs_orig = obj(
        n1        = obj(nodes=1),
        n1_p1     = obj(nodes=1,processes_per_node=1),
        n2        = obj(nodes=2),
        n2_t2     = obj(nodes=2,threads=2),
        n2_t2_p2  = obj(nodes=2,threads=2,processes_per_node=2),
        n2_t2_e   = obj(nodes=2,threads=2,env=obj(ENV_VAR=1)),
        )
    for name in sorted(supercomputers.keys()):
        m = supercomputers[name]
        if m.requires_account:
            acc = 'ABC123'
        else:
            acc = None
        #end if
        job_inputs = job_inputs_orig
        if name=='summit': # exceptional treatment for summit nodes
            job_inputs = job_inputs_orig.copy()
            jtypes = list(job_inputs.keys())
            for jtype in jtypes:
                if 'p' in jtype:
                    del job_inputs[jtype]
                else:
                    jcpu = job_inputs[jtype]
                    jcpu.gpus = 0
                    jgpu = jcpu.copy()
                    jgpu.gpus = 6
                    job_inputs[jtype+'_g6'] = jgpu
                #end if
            #end for
        #end if
        for jtype in sorted(job_inputs.keys()):
            job = Job(app_command = 'test.x',
                      machine     = name,
                      account     = acc,
                      **job_inputs[jtype]
                      )
            command = job.run_command()
            if testing.global_data['job_ref_table']:
                sname = "'{0}'".format(name)
                stype = "'{0}'".format(jtype)
                print("        ({0:<16} , {1:<16}) : '{2}',".format(sname,stype,command))
                continue
            #end if
            ref_command = job_run_ref[name,jtype]
            if not job_commands_equal(command,ref_command):
                failed('Job.run_command for machine "{0}" does not match the reference\njob inputs: {1}\nreference command: {2}\nincorrect command: {3}'.format(name,job_inputs[jtype],ref_command,command))
            #end for
        #end for
    #end for


    # test split_nodes
    for name in sorted(supercomputers.keys()):
        m = supercomputers[name]
        if m.app_launcher=='srun': # no slurm support yet
            continue
        #end if
        if name=='summit': # no summit support
            continue
        #end if
        if m.requires_account:
            acc = 'ABC123'
        else:
            acc = None
        #end if
        # make a 4 node job
        job = Job(app_command = 'test.x',
                  machine     = name,
                  account     = acc,
                  nodes       = 4,
                  threads     = m.cores_per_node,
                  )
        # split the job into 1 and 3 nodes
        job1,job2 = job.split_nodes(1)
        # get the split run commands
        rc  = job.run_command()
        rc1 = job1.run_command()
        rc2 = job2.run_command()
        ns  = ' {0} '.format(job.nodes)
        ns1 = ' {0} '.format(job1.nodes)
        ns2 = ' {0} '.format(job2.nodes)
        # verify that node count is in each command
        assert(ns  in rc )
        assert(ns1 in rc1)
        assert(ns2 in rc2)
        # verify that text on either side of node count 
        # agrees for original and split commands
        rcl ,rcr  = rc.split(ns,1)
        rc1l,rc1r = rc1.split(ns1,1)
        rc2l,rc2r = rc2.split(ns2,1)
        rcf  = rcl+' '+rcr
        rc1f = rc1l+' '+rc1r
        rc2f = rc2l+' '+rc2r
        assert(job_commands_equal(rcf,rc1f))
        assert(job_commands_equal(rcf,rc2f))
    #end for

    Machine.allow_warnings = allow_warn
#end def test_job_run_command


