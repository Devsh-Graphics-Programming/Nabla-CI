#"C:/Users/Hazard/Nabla/ci/"
#"C:/Users/Hazard/Nabla/ci/22.RaytracedAO/renders/private"

from pathlib import Path
import subprocess

# Directories of repositories
NBL_CI_DIR = '@_NBL_CI_ROOT_@'
NBL_CU_REF_DIR = NBL_CI_DIR + "/22.RaytracedAO/renders/private"


def shell(cmd):
    subprocess.run(cmd)


def CommitPublicReferenceChanges():
    shell(f'git -C "{NBL_CI_DIR}" git add .\references\* ')
    shell(f'git -C "{NBL_CI_DIR}" commit -m "Updated public references"')
    shell(f'git -C "{NBL_CI_DIR}" push')

    #shell(f'git -C "{NBL_CI_DIR}" push')


def CommitPrivateReferenceChanges():
    shell(f'git -C "{NBL_CU_REF_DIR}" git add * ')
    shell(f'git -C "{NBL_CU_REF_DIR}" commit -m "Updated private references"')
    shell(f'git -C "{NBL_CU_REF_DIR}" push')
    #shell(f'git -C "{NBL_CI_DIR}" push')


if __name__ == '__main__':
    CommitPublicReferenceChanges()
    privpath = Path(NBL_CU_REF_DIR)
    if(privpath.exists()):
        CommitPrivateReferenceChanges()