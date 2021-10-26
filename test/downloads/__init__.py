from aexpy.env import env

oldRedo = True


def setup_module():
    global oldRedo

    oldRedo = env.redo
    env.redo = True


def teardown_module():
    env.redo = oldRedo
