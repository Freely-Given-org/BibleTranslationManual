#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# assemble_markdown.py
#
# Module handling BibleTranslationManual functions
#
# Copyright (C) 2022 Robert Hunt
# Author: Robert Hunt <Freely.Given.org+BOS@gmail.com>
# License: See gpl-3.0.txt
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Module handling BibleTranslationManual functions.
"""
from typing import Dict, List, Tuple
import os
import logging
from pathlib import Path


import yaml
import cloudconvert

import secrets
import BibleOrgSysGlobals
from BibleOrgSysGlobals import fnPrint, vPrint, dPrint


LAST_MODIFIED_DATE = '2022-04-14' # by RJH
SHORT_PROGRAM_NAME = "BibleTranslationManual"
PROGRAM_NAME = "Bible Translation Manual handler"
PROGRAM_VERSION = '0.03'
programNameVersion = f'{SHORT_PROGRAM_NAME} v{PROGRAM_VERSION}'

debuggingThisModule = False

MD_SOURCE_FOLDERPATH = Path('../../originalMarkdownSources/')
COMBINED_MD_FILEPATH = Path('../../derivedFiles/BibleTranslationManual.md')
CONVERTED_ODT_FILEPATH = Path('../../derivedFiles/BibleTranslationManual.odt')
CONVERTED_PDF_FILEPATH = Path('../../derivedFiles/BibleTranslationManual.pdf')


def main() -> None:
    """
    """
    BibleOrgSysGlobals.introduceProgram( __name__, programNameVersion, LAST_MODIFIED_DATE )

    # Load manifest
    with open(MD_SOURCE_FOLDERPATH.joinpath('manifest.yaml'), 'rt') as yaml_manifest_file:
        manifest_dict = yaml.safe_load(yaml_manifest_file)
    # print(f"{manifest=}")

    markdown_doc = combine_markdown(manifest_dict)
    adjusted_doc = adjust_document(markdown_doc)

    vPrint('Quiet', debuggingThisModule, f"\nWriting {len(adjusted_doc):,} chars to {COMBINED_MD_FILEPATH}…")
    with open(COMBINED_MD_FILEPATH, 'wt') as output_file:
        output_file.write(adjusted_doc)

    if BibleOrgSysGlobals.commandLineArguments.export:
        convert_to_odt_and_pdf(adjusted_doc)
    else: vPrint('Normal', debuggingThisModule, "Use the export command-line flag to create ODT and PDF files.")
# end of main()


def combine_markdown(manifest_dict: dict) -> str:
    fnPrint(debuggingThisModule, f"combine_markdown( ({len(manifest_dict)}) )")

    markdown_docs = ["***NOTE***: Links in this document are not adjusted yet.\n"]
    for project in manifest_dict['projects']:
        # print(f"\n\n{project=}")
        vPrint('Normal', debuggingThisModule, f"Loading '{project['identifier']}' section…")
        markdown_docs.append(f"# {project['title']}\n")

        with open(MD_SOURCE_FOLDERPATH.joinpath(f"{project['path']}/toc.yaml"), 'rt') as yaml_toc_file:
            table_of_contents = yaml.safe_load(yaml_toc_file)
        # print(f"{table_of_contents=}")

        def process_section(current_path: Path, yaml_contents: dict) -> None:
            # Recursive function
            # print(f"process_section({current_path}, {yaml_contents})…")
            assert isinstance(yaml_contents, dict)
            for somekey, somevalue in yaml_contents.items():
                # print(f"  process_section() has '{somekey}'={somevalue}")
                if somekey == 'title':
                    # markdown_docs.append(f"## YAML Title: {somevalue}")
                    yaml_title = somevalue
                elif somekey == 'sections':
                    assert isinstance(somevalue, list)
                    for section in somevalue:
                        process_section(current_path, section)
                elif somekey == 'link':
                    with open(current_path.joinpath(f"{somevalue}/title.md"), 'rt') as markdown_file:
                        title = markdown_file.read().rstrip('\n')
                    if title != yaml_title:
                        logging.warning(f"md title '{title}' is different from\n       yaml title '{yaml_title}'")
                    # print(f" {title=}")
                    markdown_docs.append(f"## {title}\n")
                    with open(current_path.joinpath(f"{somevalue}/sub-title.md"), 'rt') as markdown_file:
                        answers_question = markdown_file.read().rstrip('\n')
                        if not answers_question.endswith('?'):
                            logging.warning(f"is answers_question a question?: '{answers_question}'")
                    # print(f"  {answers_question=}")
                    markdown_docs.append(f"Answers question: **{answers_question}**\n")
                    with open(current_path.joinpath(f"{somevalue}/01.md"), 'rt') as markdown_file:
                        content = markdown_file.read()
                    # print(f"    {content=}")
                    markdown_docs.append(content)
                else: logging.error(f"process_section not handling '{somekey}'")

        process_section(MD_SOURCE_FOLDERPATH.joinpath(project['path']), table_of_contents) # recursive

    vPrint('Normal', debuggingThisModule, f"\nAssembled {len(markdown_docs):,} markdown document portions.")
    markdown_doc = '\n\n'.join(markdown_docs).replace('\n\n\n','\n\n')
    vPrint('Normal', debuggingThisModule, f"  Assembled markdown doc is {len(markdown_doc):,} chars.")
    return markdown_doc
# end of combine_markdown function


def adjust_document(markdown_doc: str) -> str:
    fnPrint(debuggingThisModule, f"adjust_document( ({len(markdown_doc):,}) )")
    # Adjust our name for the manual
    ourName = 'the Bible Translation Manual'
    adjusted_doc = markdown_doc \
                    .replace('unfoldingWord® Translation Academy', ourName) \
                    .replace('Translation Academy', ourName) \
                    .replace('translationAcademy', ourName) \
                    .replace(f'\n{ourName}',f'\n{ourName[0].upper()}{ourName[1:]}')

    # Adjust links
    logging.critical("Link adjustments not done yet!")

    return adjusted_doc
# end of adjust_document function


def convert_to_odt_and_pdf(markdown_doc: str):
    fnPrint(debuggingThisModule, f"convert_to_odt( ({len(markdown_doc):,}) )")

    vPrint('Normal', debuggingThisModule, f"\nUsing CloudConvert to convert markdown document…")
    cloudconvert.configure(api_key=secrets.cloudconvert_API_key)

    job = cloudconvert.Job.create(payload={
        'tasks': {
            'upload-md-file': {
                'operation': 'import/upload',
                'input_format': 'md',
            # 'import-my-file': {
            #     'operation': 'import/url',
            #     'url': 'https://my-url'
            },
            'convert-md-file-to-odt': {
                'operation': 'convert',
                'input': 'upload-md-file',
                'output_format': 'odt',
                # 'some_other_option': 'value'
            },
            'export-odt-file': {
                'operation': 'export/url',
                'input': 'convert-md-file-to-odt',
            },
            'convert-md-file-to-pdf': {
                'operation': 'convert',
                # 'input': 'upload-md-file', # This seems to fail
                'input': 'convert-md-file-to-odt', # Try this instead
                'output_format': 'pdf',
                # 'some_other_option': 'value'
            },
            'export-pdf-file': {
                'operation': 'export/url',
                'input': 'convert-md-file-to-pdf',
            },
        }
    })

    # Upload the source file
    vPrint('Info', debuggingThisModule, f"  Uploading md file to CloudConvert…")
    upload_task_id = job['tasks'][0]['id']
    vPrint('Never', debuggingThisModule, f"    {upload_task_id=}")
    upload_task = cloudconvert.Task.find(id=upload_task_id)
    vPrint('Debug', debuggingThisModule, f"    {upload_task=}")
    md_upload_success_flag = cloudconvert.Task.upload(file_name=COMBINED_MD_FILEPATH, task=upload_task)
    vPrint('Normal', debuggingThisModule, f"    {md_upload_success_flag=}") # True

    if debuggingThisModule:
        converting_odt_url_task_id = job['tasks'][1]['id']
        converting_odt_url_task_dict = cloudconvert.Task.find(id=converting_odt_url_task_id)
        vPrint('Info', debuggingThisModule, f"    {converting_odt_url_task_dict=}") # 

    # Download the .odt output file
    vPrint('Normal', debuggingThisModule, f"  Waiting for and downloading odt file from CloudConvert…")
    exported_odt_url_task_id = job['tasks'][2]['id']
    vPrint('Never', debuggingThisModule, f"    {exported_odt_url_task_id=}")
    odt_task_dict = cloudconvert.Task.wait(id=exported_odt_url_task_id)  # Wait for job completion
    if debuggingThisModule or odt_task_dict.get('status') != 'finished':
        vPrint('Info', debuggingThisModule, f"    {odt_task_dict=}")
    odt_file_dict = odt_task_dict.get('result').get('files')[0]
    vPrint('Verbose', debuggingThisModule, f"    {odt_file_dict=}")
    saved_odt_filename = cloudconvert.download(filename=odt_file_dict['filename'], url=odt_file_dict['url'])
    # NOTE: The above saves BibleTranslationManual.odt into the current folder
    vPrint('Verbose', debuggingThisModule, f"    {saved_odt_filename=}")
    vPrint('Quiet', debuggingThisModule, f"  Moving ODT file ({odt_file_dict.get('size'):,} chars) to {CONVERTED_ODT_FILEPATH}…")
    os.replace(saved_odt_filename, CONVERTED_ODT_FILEPATH) # Overwrites any existing file

    if debuggingThisModule:
        converting_pdf_url_task_id = job['tasks'][3]['id']
        converting_pdf_url_task_dict = cloudconvert.Task.find(id=converting_pdf_url_task_id)
        vPrint('Info', debuggingThisModule, f"{converting_pdf_url_task_dict=}") # 

    # Download the .pdf output file
    vPrint('Normal', debuggingThisModule, f"  Waiting for and downloading pdf file from CloudConvert…")
    exported_pdf_url_task_id = job['tasks'][4]['id']
    vPrint('Never', debuggingThisModule, f"    {exported_pdf_url_task_id=}")
    pdf_task_dict = cloudconvert.Task.wait(id=exported_pdf_url_task_id)  # Wait for job completion
    if debuggingThisModule or pdf_task_dict.get('status') != 'finished':
        vPrint('Info', debuggingThisModule, f"    {pdf_task_dict=}")
    pdf_file_dict = pdf_task_dict.get('result').get('files')[0]
    vPrint('Verbose', debuggingThisModule, f"    {pdf_file_dict=}")
    saved_pdf_filename = cloudconvert.download(filename=pdf_file_dict['filename'], url=pdf_file_dict['url'])
    vPrint('Verbose', debuggingThisModule, f"    {saved_pdf_filename=}")
    vPrint('Quiet', debuggingThisModule, f"  Moving PDF file ({pdf_file_dict.get('size'):,} chars) to {CONVERTED_PDF_FILEPATH}…")
    os.replace(saved_pdf_filename, CONVERTED_PDF_FILEPATH) # Overwrites any existing file
# end of convert_to_odt function


if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support() # Multiprocessing support for frozen Windows executables

    # Configure basic Bible Organisational System (BOS) set-up
    parser = BibleOrgSysGlobals.setup( SHORT_PROGRAM_NAME, PROGRAM_VERSION, LAST_MODIFIED_DATE )
    BibleOrgSysGlobals.addStandardOptionsAndProcess( parser, exportAvailable=True )

    main()

    BibleOrgSysGlobals.closedown( PROGRAM_NAME, PROGRAM_VERSION )
# end of assemble_markdown.py
