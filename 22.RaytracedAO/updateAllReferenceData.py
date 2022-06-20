import os
import subprocess
import shutil
import filecmp
from datetime import datetime
from pathlib import *
import sys

NBL_PATHTRACER_EXE = Path('@_NBL_PATHTRACER_EXE_@')
NBL_CI_ROOT = '@_NBL_CI_ROOT_@' + "/22.RaytracedAO"
NBL_CI_LDS_CACHE_FILENAME = 'LowDiscrepancySequenceCache.bin'
 
NBL_CI_DIR = '@_NBL_CI_ROOT_@'
NBL_CU_REF_DIR = NBL_CI_DIR + "/22.RaytracedAO/renders/private"

def shell(cmd):
    subprocess.run(cmd)

def commitAndPushPublicReferences():
    shell(f'git -C "{NBL_CI_DIR}" git add .\references\* ')
    shell(f'git -C "{NBL_CI_DIR}" commit -m "Updated public references"')
    shell(f'git -C "{NBL_CI_DIR}" push')

def commitAndPushPrivateReferences():
    shell(f'git -C "{NBL_CU_REF_DIR}" git add * ')
    shell(f'git -C "{NBL_CU_REF_DIR}" commit -m "Updated private references"')
    shell(f'git -C "{NBL_CU_REF_DIR}" push')
 
class Inputs:
    def __init__(self, 
                input_file: Path,
                references_dir: str,
                storage_dir: str) -> None:
        self.input_file_path = Path(input_file).absolute()
        self.references_dir = Path(references_dir).absolute()
        self.storage_dir = Path(storage_dir).absolute()

NBL_SCENES_INPUTS = [ 
    Inputs(
            input_file='@_NBL_SCENES_INPUT_TXT_@',
            references_dir=f'{NBL_CI_ROOT}/references/public',
            storage_dir= f'{NBL_CI_ROOT}/renders/public'),

        Inputs(
            input_file='@_NBL_PRIVATE_SCENES_INPUT_TXT_@', 
            references_dir=f'{NBL_CI_ROOT}/references/private',
            storage_dir= f'{NBL_CI_ROOT}/renders/private') 
]        

def get_render_filename(line : str):
    words = line.replace('"', '').strip().split(" ")
    zip = (os.path.splitext(str(Path(" ".join(words[0:-1])).name))[0] + "_") if len(words) > 1 else "" 
    return zip + os.path.splitext(Path(words[-1]).name)[0]

def update_all_reference_data(inputParamList, commitAndPushReferences):
    if NBL_PATHTRACER_EXE.is_file():
        os.chdir(NBL_PATHTRACER_EXE.parent.absolute()) 

        for inputParams in inputParamList:
            if not inputParams.references_dir.is_dir():
                os.makedirs(inputParams.references_dir)

            if not inputParams.storage_dir.is_dir():
                os.makedirs(inputParams.storage_dir)
                
            generatedReferenceCache = str(NBL_PATHTRACER_EXE.parent.absolute()) + '/' + NBL_CI_LDS_CACHE_FILENAME
            destinationReferenceCache = str(inputParams.references_dir) + '/' + NBL_CI_LDS_CACHE_FILENAME

            sceneDummyRender = '"../ci/dummy_4096spp_128depth.xml"'
            executor = str(NBL_PATHTRACER_EXE.absolute()) + ' -SCENE=' + sceneDummyRender + ' -TERMINATE'
            subprocess.run(executor, capture_output=True)
                
            shutil.copyfile(generatedReferenceCache, destinationReferenceCache)
         
            input_filepath = inputParams.input_file_path
            if not input_filepath.is_file():
                print(f'Scenes input {str(input_filepath)} does not exist!')
                continue
        
            with open(input_filepath.absolute()) as aFile:
                inputLines = aFile.readlines()

            for line in inputLines:
                if list(line)[0] != ';':
                    renderName = get_render_filename(line)
                    undenoisedTargetName = 'Render_' + renderName

                    scene = line.strip()

                    generatedUndenoisedTargetName = str(NBL_PATHTRACER_EXE.parent.absolute()) + '/' + undenoisedTargetName
                    destinationReferenceUndenoisedTargetName = str(inputParams.references_dir) + '/' + renderName + '/' + undenoisedTargetName
                
                    # run a render
                    executor = str(NBL_PATHTRACER_EXE.absolute()) + ' -SCENE=' + scene + ' -TERMINATE'
                    subprocess.run(executor, capture_output=True)
                    
                    if not Path(destinationReferenceUndenoisedTargetName).parent.is_dir():
                        os.makedirs(str(Path(destinationReferenceUndenoisedTargetName).parent.absolute()))
                        
                    # update reference renders
                    shutil.copyfile(generatedUndenoisedTargetName + '.exr', destinationReferenceUndenoisedTargetName + '.exr')
                    shutil.copyfile(generatedUndenoisedTargetName + '_albedo.exr', destinationReferenceUndenoisedTargetName + '_albedo.exr')
                    shutil.copyfile(generatedUndenoisedTargetName + '_normal.exr', destinationReferenceUndenoisedTargetName + '_normal.exr')
                    shutil.copyfile(generatedUndenoisedTargetName + '_denoised.exr',destinationReferenceUndenoisedTargetName + '_denoised.exr')

                    storageFilepath = str(inputParams.storage_dir) + '/' + undenoisedTargetName
                    shutil.move(generatedUndenoisedTargetName + '.exr', storageFilepath + '.exr')
                    shutil.move(generatedUndenoisedTargetName + '_albedo.exr', storageFilepath + '_albedo.exr')
                    shutil.move(generatedUndenoisedTargetName + '_normal.exr', storageFilepath + '_normal.exr')
                    shutil.move(generatedUndenoisedTargetName + '_denoised.exr',storageFilepath + '_denoised.exr')
        
        if commitAndPushReferences:
            commitAndPushPublicReferences()
            if Path(NBL_CU_REF_DIR).exists():
                commitAndPushPrivateReferences()
    else:
        print('Path tracer executable does not exist!')
        exit(-1)

if __name__ == '__main__':
    arguments = sys.argv[1:]
    if len(arguments):
        if arguments[0] == '--commit-and-push'
            update_all_reference_data(NBL_SCENES_INPUTS, True)
    else:
        update_all_reference_data(NBL_SCENES_INPUTS, False)