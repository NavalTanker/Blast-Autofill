import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import time
import xml.etree.ElementTree as ET
import threading

# --- Suppress NotOpenSSLWarning ---
import warnings
try:
    from urllib3.exceptions import NotOpenSSLWarning
    warnings.filterwarnings('ignore', category=NotOpenSSLWarning)
except ImportError:
    pass

# --- Configuration Constants ---
NCBI_BLAST_API_URL = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
NCBI_EUTILS_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
DEFAULT_BLAST_FORMAT_TYPE = "XML"
DEFAULT_BLAST_PROGRAM = "blastn"
DEFAULT_BLASTN_DATABASE = "nt"
DEFAULT_BLASTX_DATABASE = "nr"
DEFAULT_EST_DATABASE = "est"
BLAST_POLL_INTERVAL_SECONDS = 10
BLAST_MAX_UNKNOWN_RETRIES = 5
NCBI_API_REQUEST_DELAY_SECONDS = 1
MAX_TOTAL_POLLS = 30

# --- Data Model (BlastHit) ---
class BlastHit:
    def __init__(self, accession: Optional[str] = None, hit_def_raw: Optional[str] = None,
                 definition: Optional[str] = None, organism: Optional[str] = None,
                 query_start: Optional[str] = None, query_start_base: Optional[str] = None,
                 query_end: Optional[str] = None, query_end_base: Optional[str] = None,
                 e_value: Optional[str] = None, hsp_details: Optional[Dict[str, any]] = None):
        self.accession = accession
        self.hit_def_raw = hit_def_raw
        self.definition = definition
        self.organism = organism
        self.query_start = query_start
        self.query_start_base = query_start_base
        self.query_end = query_end
        self.query_end_base = query_end_base
        self.e_value = e_value
        self.hsp_details = hsp_details if hsp_details is not None else {}
    def __repr__(self):
        return (f"BlastHit(accession='{self.accession}', organism='{self.organism}', "
                f"e_value='{self.e_value}', definition='{self.definition[:30] if self.definition else 'N/A'}...')")

# --- Helper Functions ---
def format_evalue_static(e_value_str: str) -> str:
    if not e_value_str: return "N/A"
    try:
        e_value_float = float(e_value_str)
        if e_value_float == 0.0: return "0"
        sci_notation = f"{e_value_float:e}"
        parts = sci_notation.split('e')
        significand_str, exponent_val = parts[0], int(parts[1])
        rounded_digit = round(float(significand_str))
        if abs(rounded_digit) >= 10:
            exponent_val += 1
            rounded_digit /= 10
        return f"{int(rounded_digit)}e{exponent_val}"
    except: return e_value_str

def parse_ncbi_hit_id_static(hit_id_text: str) -> str:
    if not hit_id_text: return "N/A"
    parts = hit_id_text.split('|')
    known_prefixes = ["ref", "pdb", "sp", "gb", "emb", "dbj", "prf", "tpg"]
    if len(parts) >= 4 and parts[2] in known_prefixes: return parts[3]
    if len(parts) >= 2 and parts[0] in known_prefixes: return parts[1]
    if len(parts) == 1 and not any(p in hit_id_text for p in [f"{pref}|" for pref in known_prefixes] + ["gi|"]): return hit_id_text
    if parts:
        potential_acc = parts[-1].strip()
        if potential_acc: return potential_acc
        if len(parts) > 1 and parts[-2].strip(): return parts[-2].strip()
    return hit_id_text


class BlastApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NCBI BLAST GUI Client")
        self.root.geometry("900x700")

        self.sequence_var = tk.StringVar()
        self.program_var = tk.StringVar(value="blastn")
        self.database_var = tk.StringVar(value="nt")
        self.exclude_landoltia_var = tk.BooleanVar()
        self.def_format_var = tk.StringVar(value="full")
        self.max_detail_hits_var = tk.IntVar(value=20)
        self.target_results_var = tk.IntVar(value=3)

        self.PROGRAM_OPTIONS = ["blastn", "blastx"]
        self.DATABASE_OPTIONS_BLASTN = ["nt", "est", "refseq_rna"]
        self.DATABASE_OPTIONS_BLASTX = ["nr", "refseq_protein", "swissprot"]
        self.DEF_FORMAT_OPTIONS = ["full", "short"]
        self.DEFAULT_DNA_SEQUENCE = "AGGAGAAGAAGAAAGAGGAGGAGAAACAGTCGACGTCTTCGTTTCTTACTCTGCATTCTGCGGGTGAATTCATGGACCGTGTGAAGAGGCTGAGCACGCAGAAGGCGGTGGTGATATTCAGCTCGAGCTCGTGCTGCATGTGCCACGCAGTCAAGGCCTTCTTCCAGGATCTCGGGGTGAACTACGCCGCCTACGAGCTCGACGAGGAACCCCACGGAAGGGAGATGGAGAAGGCTCTTCTCCGGCTAGTCGGCCGGAACCCGCCATTTCCGGCAGTCTACATCGGCGGCAAGCTTGTCGGCCCGACAGACCGCGTCATGTCCCTCCATCTCAGTGGCAAGCTTATGCCCATGCTGCGGGAAGCAGGCGCTAAATGGCTGTAGTCAGGCTCTCTGCGAAACCCTAACGCTAGCGGCTCTCGGTTAACCTGTGTTGACAAGTGGGCCGCGCTCTGTAGTCGTGCTCTTAAATGGGCTTGGGCCCGTGCTCCGTTTCATCTCCGTTTCTCTCCCAAAAGCAAATCCGTCCGTTAGAGTCGCACGTGGGGGAATCGGCAGACACGTGGATCTTCTTCTGTCAGAAATCGGCCTGACATTCCTCGTGGGCTTTTTCTTAATGGACTACTTACTTCGGCCCGCCTCTCAGATCGGCGAGCCCTCCTATGTACTCGGGCAGTTTAATTAATTTACAATTAATTAACCAAAAAAAAAAAAAAAAAAAAAAAAAA"
        self.sequence_var.set(self.DEFAULT_DNA_SEQUENCE)
        self.create_widgets()

    def create_widgets(self):
        main_pane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        controls_frame = ttk.LabelFrame(main_pane, text="BLAST Parameters", padding=10)
        main_pane.add(controls_frame, weight=1)

        seq_label = ttk.Label(controls_frame, text="Sequence:")
        seq_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.sequence_text = scrolledtext.ScrolledText(controls_frame, wrap=tk.WORD, height=10, width=70)
        self.sequence_text.grid(row=0, column=1, columnspan=3, sticky="ew", padx=5, pady=5)
        self.sequence_text.insert(tk.END, self.sequence_var.get())
        self.sequence_text.focus_set() # Set initial focus

        program_label = ttk.Label(controls_frame, text="Program:")
        program_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.program_combo = ttk.Combobox(controls_frame, textvariable=self.program_var, values=self.PROGRAM_OPTIONS, state="readonly", width=15)
        self.program_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.program_combo.bind("<<ComboboxSelected>>", self.update_database_options)

        db_label = ttk.Label(controls_frame, text="Database:")
        db_label.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.db_combo = ttk.Combobox(controls_frame, textvariable=self.database_var, state="readonly", width=15)
        self.db_combo.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        self.update_database_options()

        self.exclude_landoltia_check = ttk.Checkbutton(controls_frame, text="Exclude Landoltia punctata", variable=self.exclude_landoltia_var)
        self.exclude_landoltia_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        def_format_label = ttk.Label(controls_frame, text="Definition Format:")
        def_format_label.grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.def_format_combo = ttk.Combobox(controls_frame, textvariable=self.def_format_var, values=self.DEF_FORMAT_OPTIONS, state="readonly", width=10)
        self.def_format_combo.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)

        max_hits_label = ttk.Label(controls_frame, text="Max Detail Hits:")
        max_hits_label.grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_hits_spinbox = ttk.Spinbox(controls_frame, from_=1, to=500, textvariable=self.max_detail_hits_var, width=7)
        self.max_hits_spinbox.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        target_results_label = ttk.Label(controls_frame, text="Target Final Results:")
        target_results_label.grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        self.target_results_spinbox = ttk.Spinbox(controls_frame, from_=1, to=50, textvariable=self.target_results_var, width=7)
        self.target_results_spinbox.grid(row=3, column=3, sticky=tk.W, padx=5, pady=5)

        self.run_button = ttk.Button(controls_frame, text="Run BLAST", command=self.start_blast_thread)
        self.run_button.grid(row=4, column=1, columnspan=2, pady=10)

        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(3, weight=1)

        output_pane = ttk.PanedWindow(main_pane, orient=tk.HORIZONTAL)
        main_pane.add(output_pane, weight=2)

        status_frame = ttk.LabelFrame(output_pane, text="Status Log", padding=10)
        output_pane.add(status_frame, weight=1)
        self.status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=10, width=40, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True)

        results_frame = ttk.LabelFrame(output_pane, text="Results", padding=10)
        output_pane.add(results_frame, weight=2)

        columns = ("accession", "definition", "organism", "query_start", "query_end", "e_value")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")

        for col in columns: self.results_tree.heading(col, text=col.replace("_", " ").title())
        self.results_tree.column("accession", width=100, anchor=tk.W)
        self.results_tree.column("definition", width=250, anchor=tk.W)
        self.results_tree.column("organism", width=150, anchor=tk.W)
        self.results_tree.column("query_start", width=80, anchor=tk.CENTER)
        self.results_tree.column("query_end", width=80, anchor=tk.CENTER)
        self.results_tree.column("e_value", width=80, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y); hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.results_tree.pack(fill=tk.BOTH, expand=True)

    def update_database_options(self, event=None):
        program = self.program_var.get()
        if program == "blastn":
            self.db_combo['values'] = self.DATABASE_OPTIONS_BLASTN
            if self.database_var.get() not in self.DATABASE_OPTIONS_BLASTN:
                self.database_var.set(self.DATABASE_OPTIONS_BLASTN[0])
        elif program == "blastx":
            self.db_combo['values'] = self.DATABASE_OPTIONS_BLASTX
            if self.database_var.get() not in self.DATABASE_OPTIONS_BLASTX:
                self.database_var.set(self.DATABASE_OPTIONS_BLASTX[0])
        else: self.db_combo['values'] = []

    def start_blast_thread(self):
        self.run_button.config(state=tk.DISABLED)
        self.log_status("Initiating BLAST search...")
        self.clear_results_tree()
        current_sequence = self.sequence_text.get("1.0", tk.END).strip()
        if not current_sequence:
            messagebox.showerror("Input Error", "Sequence cannot be empty.")
            self.run_button.config(state=tk.NORMAL); return
        try:
            max_hits = int(self.max_detail_hits_var.get())
            target_res = int(self.target_results_var.get())
        except ValueError:
            messagebox.showerror("Input Error", "Max Detail Hits and Target Final Results must be integers.")
            self.run_button.config(state=tk.NORMAL); return

        params = (current_sequence, self.program_var.get(), self.database_var.get(),
                  self.exclude_landoltia_var.get(), self.def_format_var.get(),
                  max_hits, target_res)
        self.log_status(f"Params: Prog={params[1]}, DB={params[2]}, SeqLen={len(params[0])}, ExclLand={params[3]}, DefFmt={params[4]}, MaxHits={params[5]}, TargetRes={params[6]}")

        thread = threading.Thread(target=self._orchestrate_blast_search, args=params, daemon=True)
        thread.start()

    def log_status(self, message):
        self.root.after_idle(self._do_log_status, message)

    def _do_log_status(self, message):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

    def _submit_blast_search(self, sequence: str, database: str, program: str) -> str:
        self.log_status(f"Submitting BLAST {program} to {database}...")
        params = {"CMD": "Put", "PROGRAM": program, "DATABASE": database, "QUERY": sequence, "FORMAT_TYPE": DEFAULT_BLAST_FORMAT_TYPE}
        if program == "blastn" and database == "nt": params["NO_DATABASE_OVERRIDE"] = "true"
        if program == "blastx": params["FILTER"] = "F"
        response = requests.post(NCBI_BLAST_API_URL, params=params)
        response.raise_for_status()
        rid = None
        for line in response.text.splitlines():
            if "RID =" in line: rid = line.split("RID =")[1].strip().split(" ")[0]; break
        if not rid:
            try:
                root = ET.fromstring(response.content)
                q_node = root if root.tag=='QBlastInfo' else root.find(".//QBlastInfo")
                if q_node is not None: rid_el = q_node.find('Rid'); rid = rid_el.text.strip() if rid_el is not None and rid_el.text else None
            except ET.ParseError as e: self.log_status(f"XML ParseError (RID): {e}")
        if not rid: self.log_status(f"Error: No RID. Resp: {response.text[:200]}"); raise ValueError("No RID")
        self.log_status(f"Search submitted. RID: {rid}"); return rid

    def _check_blast_status(self, rid: str) -> str:
        self.log_status(f"Checking status for RID: {rid}...")
        params = {"CMD": "Get", "RID": rid, "FORMAT_OBJECT": "SearchInfo"}
        response = requests.get(NCBI_BLAST_API_URL, params=params); response.raise_for_status()
        status, px = "UNKNOWN", False
        try:
            root = ET.fromstring(response.content)
            q_node = root if root.tag == 'QBlastInfo' else root.find(".//QBlastInfo")
            if q_node is not None: stat_el = q_node.find('Status'); status = stat_el.text.strip().upper() if stat_el is not None and stat_el.text else "UNKNOWN"; px=True
        except ET.ParseError as e: self.log_status(f"XML ParseError (Status): {e}")
        if not px and "Status=" in response.text:
            for line in response.text.splitlines():
                if "Status=" in line: status = line.split("Status=")[1].strip().split(" ")[0].split("<")[0].strip().upper(); break
        self.log_status(f"Status for {rid}: {status}"); return status

    def _get_blast_results_xml(self, rid: str) -> str:
        self.log_status(f"Retrieving results for RID: {rid}..."); params = {"CMD": "Get", "RID": rid, "FORMAT_TYPE": DEFAULT_BLAST_FORMAT_TYPE}
        response = requests.get(NCBI_BLAST_API_URL, params=params); response.raise_for_status()
        self.log_status("Results XML retrieved."); return response.text

    def _parse_blast_xml_to_hits(self, xml_results: str, query_sequence: str) -> List[BlastHit]:
        self.log_status("Parsing BLAST XML results..."); hits: List[BlastHit] = []
        try:
            root = ET.fromstring(xml_results)
            for iter_node in root.findall('.//Iteration'):
                for hit_xml in iter_node.findall('.//Hit'):
                    hit_id = hit_xml.findtext('Hit_id', "")
                    acc_id = parse_ncbi_hit_id_static(hit_id)
                    acc_tag = hit_xml.findtext('Hit_accession')
                    accession = acc_id if "." in acc_id and acc_id!="N/A" else acc_tag or acc_id or "N/A"
                    hsp = hit_xml.find('.//Hsp')
                    if hsp:
                        qf, qt = hsp.findtext('Hsp_query-from'), hsp.findtext('Hsp_query-to')
                        qsb, qeb = "N/A", "N/A"
                        if qf and qt and query_sequence:
                            try: q_f,q_t=int(qf),int(qt); qsb=query_sequence[q_f-1] if 0<q_f<=len(query_sequence) else "N/A"; qeb=query_sequence[q_t-1] if 0<q_t<=len(query_sequence) else "N/A"
                            except: pass
                        hits.append(BlastHit(accession=accession, hit_def_raw=hit_xml.findtext('Hit_def'), query_start=qf, query_start_base=qsb, query_end=qt, query_end_base=qeb, e_value=hsp.findtext('Hsp_evalue')))
        except ET.ParseError as e: self.log_status(f"XML ParseError (Hits): {e}")
        self.log_status(f"Parsed {len(hits)} initial hits."); return hits

    def _fetch_sequence_details(self, accession: str, db_type: str) -> Dict[str, str]:
        self.log_status(f"Fetching details for {accession} (db: {db_type})...")
        if not accession or accession=="N/A": return {"Definition":"N/A", "Organism":"N/A"}
        params = {"db":db_type, "id":accession, "rettype":"gb", "retmode":"text"}
        try:
            resp = requests.get(NCBI_EUTILS_EFETCH_URL, params=params); resp.raise_for_status()
            content, def_lines, org, cap_def = resp.text, [], "N/A", False
            for line in content.splitlines():
                if line.startswith("DEFINITION"): def_lines.append(line[10:].strip()); cap_def=True
                elif cap_def:
                    if line.startswith(("ACCESSION","VERSION","KEYWORDS","SOURCE")) or line.strip().startswith("ORGANISM"): cap_def=False
                    else: def_lines.append(line.strip())
                if line.strip().startswith("ORGANISM"): parts=line.split("ORGANISM",1); org=parts[1].strip() if len(parts)>1 else "N/A"
            return {"Definition":" ".join(def_lines) or "N/A", "Organism":org}
        except requests.exceptions.RequestException as e: self.log_status(f"HTTP Err {accession}: {e}"); return {"Definition":"Err fetch", "Organism":"Err fetch"}
        except Exception as e: self.log_status(f"Parse Err {accession}: {e}"); return {"Definition":"Err parse", "Organism":"Err parse"}

    def _orchestrate_blast_search(self, current_sequence, program, database, exclude_landoltia,
                                 def_format, max_detail_hits, target_results):
        self.log_status("Orchestrating BLAST search...")
        try:
            rid = self._submit_blast_search(current_sequence, database, program)
            poll_count, unknown_status_count = 0,0
            while True:
                poll_count+=1
                if poll_count > MAX_TOTAL_POLLS: self.log_status(f"Max polls ({MAX_TOTAL_POLLS})"); raise Exception(f"Max polls.")
                status = self._check_blast_status(rid)
                if status == "READY": break
                if status in ["FAILED", "ERROR"]: self.log_status(f"Search {rid} failed: {status}"); raise Exception(f"Search failed: {status}")
                if status == "UNKNOWN": unknown_status_count+=1;
                if unknown_status_count >= BLAST_MAX_UNKNOWN_RETRIES: self.log_status("Too many UNKNOWNs"); raise Exception("Too many UNKNOWNs.")
                else: unknown_status_count=0
                # self.root.update_idletasks() # Less critical now, GUI updates are scheduled
                time.sleep(BLAST_POLL_INTERVAL_SECONDS)

            xml_data = self._get_blast_results_xml(rid)
            initial_hits = self._parse_blast_xml_to_hits(xml_data, current_sequence)
            if not initial_hits: self.log_status("No initial hits."); self.root.after_idle(lambda: messagebox.showinfo("BLAST Complete", "No hits found.")); return

            final_results, selected_orgs = [], set()
            db_type = "protein" if program == "blastx" else "nuccore"
            for i, hit in enumerate(initial_hits[:max_detail_hits]):
                if len(final_results) >= target_results: break
                self.log_status(f"Processing hit {i+1}/{len(initial_hits[:max_detail_hits])}: {hit.accession}")
                details = self._fetch_sequence_details(hit.accession, db_type)
                hit.organism, hit.definition = details["Organism"], details["Definition"]
                if def_format == "short" and hit.hit_def_raw and hit.hit_def_raw!="N/A": hit.definition = hit.hit_def_raw.split(" [")[0] or details["Definition"]

                if "Err" in hit.organism or "Err" in hit.definition: self.log_status(f"Skip {hit.accession} (detail err)"); time.sleep(NCBI_API_REQUEST_DELAY_SECONDS); continue
                if exclude_landoltia and hit.organism == "Landoltia punctata": self.log_status(f"Skip {hit.accession} (Landoltia)"); continue
                if hit.organism and hit.organism != "N/A" and hit.organism in selected_orgs: self.log_status(f"Skip {hit.accession} (org selected)"); continue

                final_results.append(hit)
                if hit.organism and hit.organism != "N/A" and "Err" not in hit.organism: selected_orgs.add(hit.organism)
                self.root.after_idle(self._do_display_hit_in_tree, hit)
                time.sleep(NCBI_API_REQUEST_DELAY_SECONDS)

            self.log_status(f"BLAST complete. Displayed {len(final_results)} hits.")
            if not final_results: self.root.after_idle(lambda: messagebox.showinfo("BLAST Complete", "No suitable hits after filtering."))
        except requests.exceptions.RequestException as e: self.log_status(f"Net/HTTP Err: {e}"); self.root.after_idle(lambda: messagebox.showerror("Network Error", f"{e}"))
        except ValueError as e: self.log_status(f"Value Err: {e}"); self.root.after_idle(lambda: messagebox.showerror("Value Error", f"{e}"))
        except Exception as e:
            self.log_status(f"Unexpected error: {e}")
            import traceback; tb_str=traceback.format_exc(); self.log_status(tb_str)
            self.root.after_idle(lambda: messagebox.showerror("Error", f"{e}\n\n{tb_str[:500]}..."))
        finally: self.root.after_idle(lambda: self.run_button.config(state=tk.NORMAL))

    def clear_results_tree(self):
        for item in self.results_tree.get_children(): self.results_tree.delete(item)

    def _do_display_hit_in_tree(self, hit: BlastHit):
        formatted_e = format_evalue_static(hit.e_value if hit.e_value is not None else "N/A")
        q_start = f"{hit.query_start_base or ''}{hit.query_start or 'N/A'}"
        q_end = f"{hit.query_end_base or ''}{hit.query_end or 'N/A'}"

        display_def = hit.definition or "N/A"
        if len(display_def) > 240: # Truncate long definitions for Treeview
            display_def = display_def[:237] + "..."

        self.results_tree.insert("", tk.END, values=(hit.accession or "N/A", display_def,
                                                      hit.organism or "N/A", q_start, q_end, formatted_e))

if __name__ == "__main__":
    root = tk.Tk()
    app = BlastApp(root)
    root.mainloop()
