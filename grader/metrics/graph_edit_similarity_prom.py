import os
import tempfile

PROM_SCRIPT_DIR = '/Volumes/Samsung_T5/Downloads/prom-6.9-all-platforms'
PROM_SCRIPT_NAME = 'ProM69_CLI.sh'


def generate_script(net1_path, net2_path):
    '''
    returns a TemporaryFile with script inside
    '''
    script = f'''
    System.out.println("Script started");

    net1_filename = \"{net1_path}\";
    net2_filename = \"{net2_path}\";

    pn1 = import_petri_net_from_pnml_file(net1_filename);
    pn2 = import_petri_net_from_pnml_file(net2_filename);

    sim_dist = calculate_graph_edit_distance_similarity(pn1[0], pn2[0]);

    System.out.println(sim_dist);
    System.exit(0);
    '''

    script_file = tempfile.NamedTemporaryFile()
    script_file.write(str.encode(script))
    script_file.seek(0)
    return script_file


def sim_dist_prom(net1_path, net2_path):
    '''
    :param net1_path: filepath to the 1st net
    :param net2_path: filepath to the 2nd net
    :return:
        the similarity distance number [0, 1], 0 -> the most distant, 1 -> the least distant
    '''
    script_file = generate_script(net1_path, net2_path)
    print(f'file with script: {script_file.name}')

    prev_workdir = os.curdir
    os.chdir(PROM_SCRIPT_DIR)
    cmd = './' + PROM_SCRIPT_NAME + ' -f ' + script_file.name + ' 2> /dev/null'
    stream = os.popen(cmd, mode='r')
    sim_dist = stream.readlines()[-1]

    os.chdir(prev_workdir)
    print(f"Sim dist calculated: {sim_dist}")
    return float(sim_dist)
