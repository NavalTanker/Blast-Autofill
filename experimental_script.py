# Attempt to suppress NotOpenSSLWarning by placing this at the very top
import warnings

try:
    from urllib3.exceptions import NotOpenSSLWarning

    warnings.filterwarnings('ignore', category=NotOpenSSLWarning)
except ImportError:
    pass  # urllib3 or NotOpenSSLWarning not available

import requests
import time
import xml.etree.ElementTree as ET


def submit_blast_search(sequence, database="est", program="blastn"):
    """Submits a BLAST search to NCBI and returns the Request ID (RID)."""
    url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
    params = {
        "CMD": "Put",
        "PROGRAM": program,
        "DATABASE": database,
        "QUERY": sequence,
        "FORMAT_TYPE": "XML"
    }
    if program == "blastn" and database == "nt":
        params["NO_DATABASE_OVERRIDE"] = "true"
    if program == "blastx":
        params["FILTER"] = "F"  # Explicitly disable low-complexity filter for blastx

    response = requests.post(url, params=params)
    response.raise_for_status()  # Raise an exception for bad status codes

    # Extract RID from the response
    # The RID is usually in a comment block like <!-- RID = ... -->
    # or in a QBlastInfo tag for newer versions
    rid = None
    for line in response.text.splitlines():
        if "RID =" in line:
            rid = line.split("RID =")[1].strip().split(" ")[0]
            break
    if not rid:
        # Try to find RID in QBlastInfo tag if not found in comment
        try:
            root = ET.fromstring(response.content)
            qblast_info = root.find('.//QBlastInfo')
            if qblast_info is not None:
                rid_element = qblast_info.find('Rid')
                if rid_element is not None:
                    rid = rid_element.text
        except ET.ParseError:
            pass  # Ignore parsing error if XML is not well-formed initially

    if not rid:
        raise ValueError("Could not extract RID from BLAST submission response.")
    return rid


def check_blast_status(rid):
    """Checks the status of a BLAST search."""
    url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
    params = {
        "CMD": "Get",
        "RID": rid,
        "FORMAT_OBJECT": "SearchInfo"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    # Status is usually in a QBlastInfo tag
    status = "UNKNOWN"
    if "Status=" in response.text:  # Fallback for older format
        for line in response.text.splitlines():
            if "Status=" in line:
                status = line.split("Status=")[1].strip()
                break
    else:
        try:
            root = ET.fromstring(response.content)
            qblast_info = root.find('.//QBlastInfo')
            if qblast_info is not None:
                status_element = qblast_info.find('Status')
                if status_element is not None and status_element.text is not None:
                    status = status_element.text.strip()  # Ensure to strip whitespace
        except ET.ParseError:
            # If XML parsing fails, status remains "UNKNOWN" (or what was found by fallback)
            print(
                f"Warning: Could not parse XML status response for RID {rid}. Response text (first 300 chars): {response.text[:300]}")
            pass
    return status


def get_blast_results(rid):
    """Retrieves BLAST results in XML format."""
    url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
    params = {
        "CMD": "Get",
        "RID": rid,
        "FORMAT_TYPE": "XML"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.text


def parse_initial_blast_results(xml_results, query_sequence, blast_program_choice):
    """Parses basic BLAST XML results to get Accession, Query Start, Query End, E Value,
    and the corresponding start and end bases from the query sequence.
    Handles blastx specific parsing for accession and query bases (amino acids)."""
    # This function will now only parse data directly available in the main BLAST XML.
    # Organism and full definition will be fetched later.
    results = []
    try:
        root = ET.fromstring(xml_results)
        for iteration in root.findall('.//Iteration'):
            for hit in iteration.findall('.//Hit'):
                accession = "N/A"
                if blast_program_choice == "blastx":
                    hit_id_text = hit.find('Hit_id').text if hit.find('Hit_id') is not None else ""
                    # Example Hit_id: gi|55250001|ref|NP_001005225.1|
                    # or sometimes just 'ref|NP_001005225.1|' or similar from other dbs
                    parts = hit_id_text.split('|')
                    if len(parts) >= 4 and parts[2] in ["ref", "pdb", "sp", "gb", "emb",
                                                        "dbj"]:  # Check for common prefixes
                        accession = parts[3]
                    elif len(parts) >= 2 and parts[0] in ["ref", "pdb", "sp", "gb", "emb",
                                                          "dbj"]:  # Handles cases like 'ref|ACCESSION|'
                        accession = parts[1]
                    else:  # Fallback or if ID format is simpler e.g. from command line blast XML
                        accession = hit.find('Hit_accession').text if hit.find('Hit_accession') is not None else "N/A"
                        # If it's a simple accession without version, try to retain it.
                        # If Hit_id was present but unparsable to a versioned ID, this might be non-ideal.
                        # However, typical NCBI XML2 for blastx has parseable Hit_id.
                else:  # For blastn and others
                    accession_element = hit.find('Hit_accession')
                    accession = accession_element.text if accession_element is not None else "N/A"

                hit_def_element = hit.find('Hit_def')
                raw_hit_def = hit_def_element.text if hit_def_element is not None else "N/A"

                hsp = hit.find('.//Hsp')  # Find the first HSP
                if hsp is not None:
                    query_from_text = hsp.find('Hsp_query-from').text if hsp.find(
                        'Hsp_query-from') is not None else None
                    query_to_text = hsp.find('Hsp_query-to').text if hsp.find('Hsp_query-to') is not None else None

                    query_from = "N/A"
                    query_to = "N/A"
                    query_start_base = "N/A"
                    query_end_base = "N/A"

                    if query_from_text and query_to_text:
                        try:
                            q_from = int(query_from_text)
                            q_to = int(query_to_text)
                            query_from = str(q_from)  # Keep as string for dict
                            query_to = str(q_to)  # Keep as string for dict

                            # Always use original query_sequence for start/end bases
                            if 0 < q_from <= len(query_sequence):
                                query_start_base = query_sequence[q_from - 1]
                            if 0 < q_to <= len(query_sequence):
                                query_end_base = query_sequence[q_to - 1]
                        except ValueError:
                            # query_from, query_to will remain "N/A" if int conversion fails
                            # query_start_base, query_end_base will also remain "N/A"
                            pass

                    evalue_element = hsp.find('Hsp_evalue')
                    evalue = evalue_element.text if evalue_element is not None else "N/A"

                    results.append({
                        "Accession #": accession,
                        # "Definition": initial_def, # Will be fetched from GenBank
                        # "Organism": "N/A",       # Will be fetched from GenBank
                        "Query Start": query_from,
                        "Query Start Base": query_start_base,
                        "Query End": query_to,
                        "Query End Base": query_end_base,
                        "E Value": evalue,
                        "Hit_def_raw": raw_hit_def
                    })
    except ET.ParseError as e:
        print(f"Error parsing initial BLAST XML: {e}")
        print(f"XML content being parsed (first 500 chars):\n{xml_results[:500]}...")
        return []
    return results


def fetch_genbank_data(accession):
    """Fetches and parses GenBank page for Definition and Organism."""
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id={accession}&rettype=gb&retmode=text"
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text

        definition = "N/A"
        organism = "N/A"

        definition_lines = []
        in_definition_section = False

        for line in content.splitlines():
            if line.startswith("DEFINITION"):
                # Remove "DEFINITION" keyword and leading/trailing whitespace
                definition_lines.append(line[10:].strip())
                in_definition_section = True
            elif in_definition_section:
                if line.startswith("ACCESSION"):
                    # Stop capturing if we hit ACCESSION
                    in_definition_section = False
                elif line.startswith("VERSION"):  # Another common section after DEFINITION
                    in_definition_section = False
                elif line.startswith("KEYWORDS"):  # Another common section after DEFINITION
                    in_definition_section = False
                elif line.startswith("SOURCE"):  # Another common section after DEFINITION
                    in_definition_section = False
                elif line.startswith(
                        "  ORGANISM"):  # ORGANISM is part of SOURCE, stop before it if not stopped by SOURCE directly
                    in_definition_section = False
                else:
                    # Append the line, removing leading whitespace that might be present in multi-line definitions
                    definition_lines.append(line.strip())

            if line.strip().startswith("ORGANISM"):
                # This typically follows "SOURCE" and is a separate field
                organism_line = line.split("ORGANISM")
                if len(organism_line) > 1:
                    organism = organism_line[1].strip()

        if definition_lines:
            definition = " ".join(definition_lines)

        return {"Definition": definition, "Organism": organism}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GenBank data for {accession}: {e}")
        return {"Definition": "Error fetching", "Organism": "Error fetching"}
    except Exception as e:
        print(f"Error parsing GenBank data for {accession}: {e}")
        return {"Definition": "Error parsing", "Organism": "Error parsing"}


def fetch_protein_data(accession):
    """Fetches and parses protein GenBank page for Definition and Organism."""
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=protein&id={accession}&rettype=gb&retmode=text"
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text

        definition = "N/A"
        organism = "N/A"

        definition_lines = []
        in_definition_section = False

        for line in content.splitlines():
            if line.startswith("DEFINITION"):
                definition_lines.append(line[10:].strip())
                in_definition_section = True
            elif in_definition_section:
                if line.startswith("ACCESSION"):
                    in_definition_section = False
                elif line.startswith("VERSION"):
                    in_definition_section = False
                elif line.startswith("KEYWORDS"):
                    in_definition_section = False
                elif line.startswith("SOURCE"):
                    in_definition_section = False
                elif line.startswith("  ORGANISM"):
                    in_definition_section = False
                else:
                    definition_lines.append(line.strip())

            if line.strip().startswith("ORGANISM"):
                organism_line = line.split("ORGANISM")
                if len(organism_line) > 1:
                    organism = organism_line[1].strip()

        if definition_lines:
            definition = " ".join(definition_lines)

        return {"Definition": definition, "Organism": organism}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching protein data for {accession}: {e}")
        return {"Definition": "Error fetching", "Organism": "Error fetching"}
    except Exception as e:
        print(f"Error parsing protein data for {accession}: {e}")
        return {"Definition": "Error parsing", "Organism": "Error parsing"}


if __name__ == "__main__":
    dna_sequence = "AGGAGAAGAAGAAAGAGGAGGAGAAACAGTCGACGTCTTCGTTTCTTACTCTGCATTCTGCGGGTGAATTCATGGACCGTGTGAAGAGGCTGAGCACGCAGAAGGCGGTGGTGATATTCAGCTCGAGCTCGTGCTGCATGTGCCACGCAGTCAAGGCCTTCTTCCAGGATCTCGGGGTGAACTACGCCGCCTACGAGCTCGACGAGGAACCCCACGGAAGGGAGATGGAGAAGGCTCTTCTCCGGCTAGTCGGCCGGAACCCGCCATTTCCGGCAGTCTACATCGGCGGCAAGCTTGTCGGCCCGACAGACCGCGTCATGTCCCTCCATCTCAGTGGCAAGCTTATGCCCATGCTGCGGGAAGCAGGCGCTAAATGGCTGTAGTCAGGCTCTCTGCGAAACCCTAACGCTAGCGGCTCTCGGTTAACCTGTGTTGACAAGTGGGCCGCGCTCTGTAGTCGTGCTCTTAAATGGGCTTGGGCCCGTGCTCCGTTTCATCTCCGTTTCTCTCCCAAAAGCAAATCCGTCCGTTAGAGTCGCACGTGGGGGAATCGGCAGACACGTGGATCTTCTTCTGTCAGAAATCGGCCTGACATTCCTCGTGGGCTTTTTCTTAATGGACTACTTACTTCGGCCCGCCTCTCAGATCGGCGAGCCCTCCTATGTACTCGGGCAGTTTAATTAATTTACAATTAATTAACCAAAAAAAAAAAAAAAAAAAAAAAAAA"
    # database_to_search = "est" # Will be set by user input

    # Get user input for BLAST program
    while True:
        blast_program_choice = input("Select BLAST program (blastn or blastx): ").strip().lower()
        if blast_program_choice in ["blastn", "blastx"]:
            break
        print("Invalid choice. Please enter 'blastn' or 'blastx'.")

    # Get user input for database based on program choice
    if blast_program_choice == "blastn":
        while True:
            database_choice_input = input("Select database for blastn (est or nr/nt): ").strip().lower()
            if database_choice_input == "est":
                database_to_search = "est"
                break
            elif database_choice_input == "nr/nt":
                database_to_search = "nt"  # Use "nt" for NCBI
                break
            print("Invalid choice. Please enter 'est' or 'nr/nt'.")
    else:  # blastx
        database_to_search = "nr"  # blastx typically uses nr (protein database)
        print("Using 'nr' database for blastx.")

    # User preferences
    exclude_landoltia_input = input("Exclude 'Landoltia punctata' from results? (yes/no, default no): ").strip().lower()
    exclude_landoltia = exclude_landoltia_input == "yes"

    definition_format_choice_input = input(
        "Use full-length definition or shortened version from initial BLAST hit? (full/short, default full): ").strip().lower()
    if definition_format_choice_input == "short":
        definition_format_choice = "short"
    else:
        definition_format_choice = "full"  # Default to full

    print(
        f"Submitting BLAST {blast_program_choice} search against '{database_to_search}' (NCBI name: {database_to_search})...")
    try:
        rid_value = submit_blast_search(dna_sequence, database=database_to_search, program=blast_program_choice)
        print(f"Search submitted. RID: {rid_value}")

        unknown_status_count = 0
        max_unknown_retries = 5  # Allow up to 5 consecutive UNKNOWN statuses

        while True:
            status = check_blast_status(rid_value)
            print(f"Current search status: {status}")

            if status == "READY":
                break
            elif status == "UNKNOWN":
                unknown_status_count += 1
                if unknown_status_count >= max_unknown_retries:
                    print(
                        f"Search status remained 'UNKNOWN' for {max_unknown_retries} attempts. Assuming failure or issue with RID.")
                    exit()
                print(
                    f"Status is 'UNKNOWN' (attempt {unknown_status_count}/{max_unknown_retries}). Retrying in 10 seconds...")
            elif status in ["FAILED", "ERROR"]:  # Separated UNKNOWN from this
                print(f"Search failed with status: {status}")
                exit()
            else:  # Reset unknown_status_count if status is something else (e.g. WAITING)
                unknown_status_count = 0

            time.sleep(10)

        print("Retrieving initial BLAST results...")
        xml_data = get_blast_results(rid_value)

        print("\nParsing initial BLAST results...")
        initial_hits = parse_initial_blast_results(xml_data, dna_sequence, blast_program_choice)

        if not initial_hits:
            print("No initial hits found or failed to parse.")
            exit()

        print(
            f"\nFound {len(initial_hits)} initial hits. Fetching GenBank data and filtering (processing up to top 20 initial hits for 'est' database)...")

        final_results = []
        selected_organisms = set()
        hits_processed = 0
        # Limit the number of initial hits to process to avoid excessive runtimes
        # We still aim for 3 final results from unique organisms.
        for hit in initial_hits[:100]:  # Process up to the first 100 hits
            if len(final_results) >= 3:
                break

            hits_processed += 1
            print(
                f"Processing hit {hits_processed} (Accession {hit['Accession #']}). Aiming for {3 - len(final_results)} more unique organism results.")

            details_data = None
            if blast_program_choice == "blastx":
                details_data = fetch_protein_data(hit["Accession #"])
            else:  # blastn or other nucleotide programs
                details_data = fetch_genbank_data(hit["Accession #"])

            # Check for fetch/parse errors before checking organism
            if "Error" in details_data["Organism"] or "Error" in details_data["Definition"]:
                print(f"  Skipped (Error fetching/parsing): {hit['Accession #']}")
                time.sleep(1)  # Wait after an error too
                continue

            # Assign definition based on user choice
            raw_definition = hit.get("Hit_def_raw", "")  # Get it regardless of choice for potential use

            if definition_format_choice == "short":
                current_def_portion = raw_definition
                # First, handle cases like "def1 [Org1] > def2 [Org2]" by taking text before first ">"
                if ' >' in current_def_portion:
                    current_def_portion = current_def_portion.split(' >', 1)[0].strip()

                # Then, find the text before the first "[Organism]"
                first_bracket_start = current_def_portion.find(' [')
                if first_bracket_start != -1:
                    # Check if this bracket seems to be an organism by also checking for a closing ']'
                    # This is a heuristic; a more robust way would be regex or checking against known organism list
                    # For now, just assume if '[' is found, it's relevant
                    short_def = current_def_portion[:first_bracket_start].strip()
                else:
                    # No bracket found, so the whole (potentially already ">" truncated) string is the def
                    short_def = current_def_portion.strip()

                if short_def:
                    hit["Definition"] = short_def
                else:  # Fallback if short_def is empty after all parsing attempts
                    hit["Definition"] = details_data["Definition"]
                    if raw_definition and not short_def:
                        print(
                            f"    Note: Parsed short definition for {hit['Accession #']} was empty (from '{raw_definition}'), used full definition.")
                    elif not raw_definition:
                        print(f"    Note: No raw definition available for {hit['Accession #']}, used full definition.")
            else:  # Full definition choice
                hit["Definition"] = details_data["Definition"]

            hit["Organism"] = details_data["Organism"]  # Always assign organism

            # Apply filters: optional Landoltia exclusion and unique organism
            organism_is_landoltia = details_data["Organism"] == "Landoltia punctata"

            if exclude_landoltia and organism_is_landoltia:
                print(
                    f"  Skipped (Landoltia punctata excluded by user): {hit['Accession #']} - {details_data['Organism']}")
            elif details_data["Organism"] in selected_organisms:
                print(f"  Skipped (Organism already selected): {hit['Accession #']} - {details_data['Organism']}")
            else:
                # If not excluded Landoltia (or not Landoltia at all) AND organism is new
                final_results.append(hit)
                selected_organisms.add(details_data["Organism"])
                print(f"  Added: {hit['Accession #']} - {details_data['Organism']} (New unique organism)")

            time.sleep(1)  # Be respectful to NCBI servers

        if not final_results:
            print("No results found after filtering for 'Landoltia punctata' and fetching details.")
        else:
            print("\nFinal Top 3 Results (excluding Landoltia punctata):")
            print("| Accession # | Definition | Organism | Query Start | Query End | E Value |")
            print("|---|---|---|---|---|---|")
            for item in final_results:
                # Format E value: round to one significant digit for the base, then 'e', then exponent
                try:
                    e_value_float = float(item['E Value'])
                    # Get the exponent
                    exponent = int(f"{e_value_float:e}".split('e')[-1])
                    # Get the significand and round it to the nearest integer
                    significand = round(e_value_float / (10 ** exponent))
                    formatted_e_value = f"{int(significand)}e{exponent}"
                except ValueError:
                    formatted_e_value = item['E Value']  # Fallback if not a float or other error
                except Exception:  # Catch any other formatting errors
                    formatted_e_value = item['E Value']  # Fallback
                print(
                    f"| {item['Accession #']} | {item['Definition']} | {item['Organism']} | {item['Query Start Base']}{item['Query Start']} | {item['Query End Base']}{item['Query End']} | {formatted_e_value} |")

    except requests.exceptions.RequestException as e:
        print(f"An HTTP error occurred: {e}")
    except ValueError as e:
        print(f"A value error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
