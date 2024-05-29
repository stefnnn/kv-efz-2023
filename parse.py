###
# Parse KV-EFZ Bildungsplan (v2023) from PDF / plain text to JSON
#
# Input: 
# Bildungsplan Kauffrau/Kaufmann mit eidgenössischem Fähigkeitszeugnis (EFZ)
# vom 24. Juni 2021 (Stand am 1. Juni 2023)
# URL: https://www.skkab.ch/download/bildungsplan/
# PDF: https://www.skkab.ch/download/bildungsplan/?wpdmdl=6259&refresh=664edfbc7cc9c1716445116&ind=1685604344061&filename=DE_BiPla_SKKAB_inkl_Branchenspezifika_Version-01.06.2023.pdf
#
# License: MIT
###

import json
import re
import os

# Input file path
dir = os.path.dirname(os.path.realpath(__file__))
FILE_PATH = os.getenv("FILE_PATH", os.path.join(dir, "kv-efz-2023-06-01.txt"))
OUTPUT_PATH = os.getenv("OUTPUT_PATH", FILE_PATH.replace(".txt", ".json"))
DEBUG_PRINT = os.getenv("DEBUG_PRINT", "false").lower() == "true"

# Regular expression to match competency identifiers (e.g. a1.bs1)
RX_COMPETENCY_IDENTIFIER = r'(\w\d+\.(?:bs|bt)\d+\w?)\n'
RX_AREA_IDENTIFIER = r'(Handlungskompetenzbereich [a-z]):'
RX_SECTION_IDENTIFIER = r'(Handlungskompetenz [a-z][0-9]):'

# Short helper function to clean up text from the PDF (hyphens, newlines, tabs)
def clean_text(text: str):
    return text.strip().replace('-\n', '').replace('\n', ' ').replace('\t', ' ')

# The actual parser function
def parse_plan(file_path: str) -> list[dict]:
    # Read the plain text file
    with open(file_path, 'r') as file:
        text = file.read()
        print(f"Read text file from {file_path}")
    
    # Split by main areas
    data = re.split(RX_AREA_IDENTIFIER, text)
    plan: list[dict] = []
    
    # Cycle through main areas
    for area_code, area_raw in zip(data[1::2], data[2::2]):
        # Split according to sub-sections
        content_raw = re.split(RX_SECTION_IDENTIFIER, area_raw)

        # The first element contains the area title (i.e. before the first sub-section identifier)
        area_title = clean_text(content_raw[0])
        area_data = {'code': area_code, 'title': area_title, 'sections': []}
        
        # Cycle through sub-sections
        for section_code, section_raw in zip(content_raw[1::2], content_raw[2::2]):
            # Split according to competencies, seperated by identifiers like a1.bs1
            # bs = Berufsschule, bt = Betrieb
            competencies_list = re.split(RX_COMPETENCY_IDENTIFIER, section_raw, flags=re.DOTALL)
            # The first element contains the section title (first line) and the description (rest)
            section_title, section_desc = re.split(r'\n', competencies_list[0], maxsplit=1)
            section_desc.replace(" Leistungsziele Betrieb Leistungsziele Berufsfachschule", "")
            section_data = {'code': section_code, 'title': clean_text(section_title), "desc": clean_text(section_desc), 'competencies': []}

            # Create a dictionary from the competencies
            for code, desc_raw in zip(competencies_list[1::2], competencies_list[2::2]):
                desc = clean_text(desc_raw)
                where = "Berufsschule" if "bs" in code else "Betrieb"
                competency = {"code": code, "description": desc, "where": where}
                section_data['competencies'].append(competency)
                
            
            # Append the section to the area
            area_data['sections'].append(section_data)

        # Append the area to the plan
        plan.append(area_data)

    num_sections = sum([len(area['sections']) for area in plan])
    num_competencies = sum([len(section['competencies']) for area in plan for section in area['sections']])
    print(f"Parsed {len(plan)} areas with a total of {num_sections} sections and {num_competencies} competencies.")
    return plan

# Print the parsed plan in a human-readable format
def debug_plan(parsed: list[dict]):
    for area in parsed:
        print(f'\n\n\n{area["title"].upper()}\n{60*"="}')
        for section in area['sections']:
            print(f'\n{section["code"]} - {section["title"]}\n{60*"-"}')
            for title, desc in section['competencies'].items():
                print(f'  - {title} // {desc}')

# Parse and write the plan to a JSON file
def main():
    plan = parse_plan(FILE_PATH)

    # Write output to JSON file
    with open(OUTPUT_PATH, 'w') as file:
        json.dump(plan, file, indent=2)
        print(f"Wrote parsed plan to {OUTPUT_PATH}")

    if DEBUG_PRINT: 
        debug_plan(plan)

if __name__ == '__main__':
    main()
