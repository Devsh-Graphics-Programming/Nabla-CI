import os
import subprocess
import shutil
import filecmp
from datetime import datetime
from pathlib import *

NBL_IMAGEMAGICK_EXE = Path('@_NBL_IMAGEMAGICK_EXE_@')
NBL_PATHTRACER_EXE = Path('@_NBL_PATHTRACER_EXE_@')
NBL_CI_ROOT = '@_NBL_CI_ROOT_@' + "/22.RaytracedAO"
NBL_CI_LDS_CACHE_FILENAME = 'LowDiscrepancySequenceCache.bin'
NBL_ERROR_THRESHOLD = "0.05" #relative error between reference and generated images, value between 1.0 and 0.0
NBL_ERROR_TOLERANCE_COUNT = 64   
 
def get_git_revision_hash() -> str:
    return subprocess.check_output(f'git -C "{NBL_CI_ROOT}" rev-parse HEAD').decode('ascii').strip()

def get_submodule_revision_hash() -> str:
    return subprocess.check_output(f'git -C "{NBL_CI_ROOT}" submodule status').decode('ascii').strip().split()[0]

class Inputs:
    def __init__(self, 
                input_file: Path,
                ref_url: str,
                diff_imgs_url: str,
                result_imgs_url: str,
                summary_html_filepath: Path,
                references_dir: str,
                diff_images_dir: str,
                storage_dir: str) -> None:
        self.input_file_path = Path(input_file).absolute()
        self.ref_url = ref_url
        self.diff_imgs_url = diff_imgs_url
        self.result_imgs_url = result_imgs_url
        self.summary_html_filepath = Path(summary_html_filepath).absolute()
        self.references_dir = Path(references_dir).absolute()
        self.diff_images_dir = Path(diff_images_dir).absolute()
        self.storage_dir = Path(storage_dir).absolute()

NBL_SCENES_INPUTS = [ 
    Inputs(
            input_file='@_NBL_SCENES_INPUT_TXT_@', # path to input txt
            summary_html_filepath=f'{NBL_CI_ROOT}/renders/public/index.html', 
            ref_url='https://github.com/Devsh-Graphics-Programming/Nabla-Ci/tree/'+ get_git_revision_hash() ,
            diff_imgs_url = 'https://artifactory.devsh.eu/Ditt/ci/data/renders/public/difference-images',
            result_imgs_url = 'https://artifactory.devsh.eu/Ditt/ci/data/renders/public',
            references_dir=f'{NBL_CI_ROOT}/references/public',
            diff_images_dir=f'{NBL_CI_ROOT}/renders/public/difference-images',
            storage_dir= f'{NBL_CI_ROOT}/renders/public'),

        Inputs(
            input_file='@_NBL_PRIVATE_SCENES_INPUT_TXT_@', 
            summary_html_filepath=f'{NBL_CI_ROOT}/renders/private/index.html', 
            ref_url='https://github.com/Devsh-Graphics-Programming/Ditt-Reference-Renders/tree/' + get_submodule_revision_hash(),
            diff_imgs_url = 'https://artifactory.devsh.eu/Ditt/ci/data/renders/private/difference-images',
            result_imgs_url = 'https://artifactory.devsh.eu/Ditt/ci/data/renders/private',
            references_dir=f'{NBL_CI_ROOT}/references/private',
            diff_images_dir=f'{NBL_CI_ROOT}/renders/private/difference-images',
            storage_dir= f'{NBL_CI_ROOT}/renders/private') 
]
CLOSE_TO_ZERO = "0.00001"         
CI_PASS_STATUS = True


HTML_TUPLE_RENDER_INDEX = 0
HTML_TUPLE_PASS_STATUS_INDEX = 1
HTML_TUPLE_INPUT_INDEX = 2
HTML_TUPLE_ALBEDO_INDEX = 3
HTML_TUPLE_NORMAL_INDEX = 4
HTML_TUPLE_DENOISED_INDEX = 5

HTML_R_A_N_D_D_DIFF = 0
HTML_R_A_N_D_D_ERROR = 1
HTML_R_A_N_D_D_PASS = 2
HTML_R_A_N_D_D_REF = 3
HTML_R_A_N_D_D_RES = 4

def generateHTMLStatus(_htmlData, _cacheChanged, scenes_input : Inputs):
    HTML_BODY = '''
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    table {
      font-family: arial, sans-serif;
      border-collapse: collapse;
      width: 100%;
    }
    
    td, th {
      border: 1px solid #dddddd;
      text-align: left;
      padding: 8px;
      text-align: center;
    }
    
    tr:nth-child(even) {
      background-color: #dddddd;
    }
    
    table, th, td {
        border: 1px solid black;
    }
    </style>
    </head>
    <body>
    
    <h2>Ditt Render Scenes job status</h2>
    
    '''
    
    HTML_BODY += f'''
    <p>Relative error threshold is set to <strong>{float(NBL_ERROR_THRESHOLD)*100.0}%</strong></p>
    <p>Created at {datetime.now()} </p>
    '''
    if _cacheChanged:
        HTML_BODY += '''
        <h2 style="color: red;">FAILED PASS: Low Discrepancy Sequence Cache has been overwritten by a new one!</h2>
        
        '''
    HTML_BODY += '''
    <table>
      <tr>
        <th>Render</th>
        <th>Pass status</th>
        <th colspan="3" scope="colgroup">Input</th>
        <th colspan="3" scope="colgroup">Albedo</th>
        <th colspan="3" scope="colgroup">Normal</th>
        <th colspan="3" scope="colgroup">Denoised</th>
      </tr>
    '''

    for _htmlRowTuple in _htmlData:
        HTML_ROW_BODY = '''
        <tr>
          <td>''' + _htmlRowTuple[HTML_TUPLE_RENDER_INDEX] + '</td>'

        if _htmlRowTuple[HTML_TUPLE_PASS_STATUS_INDEX]:
            HTML_ROW_BODY += '<td style="color: green;">PASSED</td>'
        else:
            HTML_ROW_BODY += '<td style="color: red;">FAILED</td>'

        for i in range(4):
            anIndexOfRenderAspect = i + HTML_TUPLE_INPUT_INDEX

            aspectRenderData = _htmlRowTuple[anIndexOfRenderAspect]
            HTML_HYPERLINK_REF = scenes_input.ref_url + '/' + _htmlRowTuple[HTML_TUPLE_RENDER_INDEX] + '/' + aspectRenderData[HTML_R_A_N_D_D_REF]
            HTML_HYPERLINK_DIFF = scenes_input.diff_imgs_url + '/' + aspectRenderData[HTML_R_A_N_D_D_DIFF]
            HTML_HYPERLINK_RES = scenes_input.result_imgs_url + '/' + aspectRenderData[HTML_R_A_N_D_D_RES]
            HTML_ROW_BODY += (  '<td scope="col">' + '<a href="' + HTML_HYPERLINK_DIFF + '">' 
                + aspectRenderData[HTML_R_A_N_D_D_DIFF] + '</a><br/>'
                '<a href="'+HTML_HYPERLINK_REF+ '">(reference)</a><br/>'
                '<a href="'+HTML_HYPERLINK_RES+ '">(result)</a>'
                '</td>' 

                '<td scope="col">Errors: ' + aspectRenderData[HTML_R_A_N_D_D_ERROR] + '</td>')
            if aspectRenderData[HTML_R_A_N_D_D_PASS]:
                HTML_ROW_BODY += '<td scope="col" style="color: green;">PASSED</td>'
            else:
                HTML_ROW_BODY += '<td scope="col" style="color: red;">FAILED</td>'
        HTML_ROW_BODY += '</tr>'

        HTML_BODY += HTML_ROW_BODY

    HTML_BODY += '''
    </table>
    </body>
    </html>
    '''

    htmlFile = open(scenes_input.summary_html_filepath, "w+")
    htmlFile.write(HTML_BODY)
    htmlFile.close()


def get_render_filename(line : str):
    words = line.replace('"', '').strip().split(" ")
    zip = (os.path.splitext(str(Path(" ".join(words[0:-1])).name))[0] + "_") if len(words) > 1 else "" 
    return zip + os.path.splitext(Path(words[-1]).name)[0]

def run_all_tests(inputParamList):
    if NBL_PATHTRACER_EXE.is_file():

        os.chdir(NBL_PATHTRACER_EXE.parent.absolute()) 

        for inputParams in inputParamList:

            if not inputParams.references_dir.is_dir():
                os.makedirs(inputParams.references_dir)

            if not inputParams.storage_dir.is_dir():
                os.makedirs(inputParams.storage_dir)
                
            if not inputParams.diff_images_dir.is_dir():
                os.makedirs(inputParams.diff_images_dir)

            NBL_DUMMY_CACHE_CASE = not bool(Path(str(inputParams.references_dir) + '/' + NBL_CI_LDS_CACHE_FILENAME).is_file())
            generatedReferenceCache = str(NBL_PATHTRACER_EXE.parent.absolute()) + '/' + NBL_CI_LDS_CACHE_FILENAME
            destinationReferenceCache = str(inputParams.references_dir) + '/' + NBL_CI_LDS_CACHE_FILENAME

            sceneDummyRender = '"../ci/dummy_4096spp_128depth.xml"'
            executor = str(NBL_PATHTRACER_EXE.absolute()) + ' -SCENE=' + sceneDummyRender + ' -TERMINATE'
            subprocess.run(executor, capture_output=True)
                
            # if we start the path tracer first time
            if NBL_DUMMY_CACHE_CASE:
                shutil.copyfile(generatedReferenceCache, destinationReferenceCache)
            elif not filecmp.cmp(destinationReferenceCache, generatedReferenceCache):
                # fail CI if the reference cache is different that current generated cache
                cacheChanged = True
                CI_PASS_STATUS = False
                # copy?
            input_filepath = inputParams.input_file_path
            if not input_filepath.is_file():
                print(f'Scenes input {str(input_filepath)} does not exist!')
                continue
        
            with open(input_filepath.absolute()) as aFile:
                inputLines = aFile.readlines()

            htmlData = []
            cacheChanged = False

            for line in inputLines:
                if list(line)[0] != ';':
                    htmlRowTuple = ['', True, ['', '', True, '', ''], ['', '', True, '', ''], ['', '', True, '', ''], ['', '', True, '', '']]
                    renderName = get_render_filename(line)
                    undenoisedTargetName = 'Render_' + renderName

                    scene = line.strip()

                    generatedUndenoisedTargetName = str(NBL_PATHTRACER_EXE.parent.absolute()) + '/' + undenoisedTargetName
                    destinationReferenceUndenoisedTargetName = str(inputParams.references_dir) + '/' + renderName + '/' + undenoisedTargetName
                
                    # dummy case executes when there is no reference image
                    NBL_DUMMY_RENDER_CASE = not bool(Path(destinationReferenceUndenoisedTargetName + '.exr').is_file())
                    # if we render first time a scene then we need to have a reference of this scene for following ci checks
                    if NBL_DUMMY_RENDER_CASE:
                        executor = str(NBL_PATHTRACER_EXE.absolute()) + ' -SCENE=' + scene + ' -TERMINATE'
                        subprocess.run(executor, capture_output=True)
                        if not Path(destinationReferenceUndenoisedTargetName).parent.is_dir():
                            os.makedirs(str(Path(destinationReferenceUndenoisedTargetName).parent.absolute()))
                        shutil.copyfile(generatedUndenoisedTargetName + '.exr', destinationReferenceUndenoisedTargetName + '.exr')
                        shutil.copyfile(generatedUndenoisedTargetName + '_albedo.exr', destinationReferenceUndenoisedTargetName + '_albedo.exr')
                        shutil.copyfile(generatedUndenoisedTargetName + '_normal.exr', destinationReferenceUndenoisedTargetName + '_normal.exr')
                        shutil.copyfile(generatedUndenoisedTargetName + '_denoised.exr',destinationReferenceUndenoisedTargetName + '_denoised.exr')

                    htmlRowTuple[HTML_TUPLE_RENDER_INDEX] = renderName
                    executor = str(NBL_PATHTRACER_EXE.absolute()) + ' -SCENE=' + scene + ' -TERMINATE'
                    subprocess.run(executor, capture_output=True)

                    if not filecmp.cmp(destinationReferenceCache, generatedReferenceCache):
                        # fail CI if the reference cache is different that current generated cache
                        cacheChanged = True
                        CI_PASS_STATUS = False

                    anIndex = HTML_TUPLE_INPUT_INDEX
                    outputDiffTerminators = ['', '_albedo', '_normal', '_denoised']
                    for diffTerminator in outputDiffTerminators:
                        imageDiffFilePath = str(inputParams.diff_images_dir) + '/' + renderName + diffTerminator + "_diff.exr"
                        imageRefFilepath = destinationReferenceUndenoisedTargetName + diffTerminator + '.exr'
                        imageGenFilepath = generatedUndenoisedTargetName + diffTerminator + '.exr'

                        #create difference image for debugging
                        diffImageCommandParams = f' "{imageRefFilepath}" "{imageGenFilepath}" -fx "abs(u-v)" -alpha off "{imageDiffFilePath}"'
                        executor = str(NBL_IMAGEMAGICK_EXE.absolute()) + diffImageCommandParams
                        subprocess.run(executor, capture_output=False)

                        #calculate the amount of pixels whose relative errors are above NBL_ERROR_THRESHOLD
                        #logic operators in image magick return 1.0 if true, 0.0 if false 
                        #image magick convert -compose divide does not work with HDRI, this requiring use of -fx 
                        diffValueCommandParams = f" {imageRefFilepath} {imageGenFilepath}  -define histogram:unique-colors=true -fx \"(min(u,v)>{CLOSE_TO_ZERO})?((abs(u-v)/min(u,v))>{NBL_ERROR_THRESHOLD}):(max(u,v)>{CLOSE_TO_ZERO})\" -format %c histogram:info:" 
                        executor = str(NBL_IMAGEMAGICK_EXE.absolute()) + diffValueCommandParams
                        magickDiffValProcess = subprocess.run(executor, capture_output=True)
                    
                        #first histogram line is the amount of black pixels - the correct ones
                        #second (and last) line is amount of white - pixels whose rel err is above NBL_ERROR_THRESHOLD
                        histogramOutputLines = magickDiffValProcess.stdout.decode().splitlines()
                        errorPixelCount = histogramOutputLines[-1].split()[0][:-1] if len(histogramOutputLines) > 1 else "0"

                        #diffValueFilepath = input.references_dir+ '/' + renderName + '/' + renderName + diffTerminator + '_diff.txt'
                        #diffValueFile = open(diffValueFilepath, "w")
                        #diffValueFile.write('difference error: ' + str(errorPixelCount))
                        #diffValueFile.close()

                        # threshold for an error, for now we fail CI when the difference is greater then NBL_ERROR_TOLERANCE_COUNT
                        DIFF_PASS = float(errorPixelCount) <= NBL_ERROR_TOLERANCE_COUNT
                        if not DIFF_PASS:
                            CI_PASS_STATUS = False
                            htmlRowTuple[HTML_TUPLE_PASS_STATUS_INDEX] = False

                        htmlRowTuple[anIndex][HTML_R_A_N_D_D_DIFF] = renderName + diffTerminator + "_diff.exr"
                        htmlRowTuple[anIndex][HTML_R_A_N_D_D_ERROR] = str(errorPixelCount)
                        htmlRowTuple[anIndex][HTML_R_A_N_D_D_PASS] = DIFF_PASS
                        htmlRowTuple[anIndex][HTML_R_A_N_D_D_REF] = 'Render_' + renderName + diffTerminator + ".exr"
                        htmlRowTuple[anIndex][HTML_R_A_N_D_D_RES] = undenoisedTargetName + diffTerminator + ".exr"

                        anIndex += 1
                    htmlData.append(htmlRowTuple)

                    storageFilepath = str(inputParams.storage_dir) + '/' + undenoisedTargetName
                    shutil.move(generatedUndenoisedTargetName + '.exr', storageFilepath + '.exr')
                    shutil.move(generatedUndenoisedTargetName + '_albedo.exr', storageFilepath + '_albedo.exr')
                    shutil.move(generatedUndenoisedTargetName + '_normal.exr', storageFilepath + '_normal.exr')
                    shutil.move(generatedUndenoisedTargetName + '_denoised.exr',storageFilepath + '_denoised.exr')


            generateHTMLStatus(htmlData, cacheChanged, inputParams)
    else:
        print('Path tracer executable does not exist!')
        exit(-1)

if __name__ == '__main__':
    run_all_tests(NBL_SCENES_INPUTS)

if not CI_PASS_STATUS:
    exit(-2)
