import os
import typing
from string import Template
import shutil
import subprocess


import pyccc
from pyccc import atom_note, page_parsing, sn, pdf, lang_convert

main_filename = "sn.tex"
suttas_filename = "suttas.tex"
localnotes_filename = "localnotes.tex"
globalnotes_filename = "globalnotes.tex"
fonttex_filename = "type-imp-myfonts.tex"
creator_note_filename = "creator_note.tex"
read_note_filename = "read_note.tex"


def write_fontstex(work_dir, fonts_dir):
    fonttex = open(os.path.join(pyccc.TEX_DIR, fonttex_filename), "r").read()
    new_fonttex = fonttex.replace("../../fonts", os.path.expanduser(fonts_dir))

    with open(os.path.join(work_dir, fonttex_filename), "w") as new_fonttex_file:
        new_fonttex_file.write(new_fonttex)


def write_main(main_file: typing.TextIO, bns, c):
    nikaya = sn.get()
    homage = pdf.join_to_tex(nikaya.homage_listline, bns, c)
    _head_t = open(os.path.join(pyccc.TEX_DIR, "sn.tex"), "r").read()
    strdate = page_parsing.lm_to_strdate(nikaya.last_modified)
    _head = Template(_head_t).substitute(date=strdate, suttas=suttas_filename,
                                         homage=homage,
                                         localnotes=localnotes_filename, globalnotes=globalnotes_filename)
    main_file.write(_head)


def write_suttas(latex_io: typing.TextIO, bns, c):
    nikaya = sn.get()

    for pian in nikaya.pians:
        latex_io.write("\\pian" +
                       "{" + c(pian.title) + "}" +
                       "{" + pian.xiangyings[0].serial + "}" +
                       "{" + pian.xiangyings[-1].serial + "}\n")

        for xiangying in pian.xiangyings:
            latex_io.write("\\xiangying" +
                           "{" + xiangying.serial + "}" +
                           "{" + c(xiangying.title) + "}\n")

            for pin in xiangying.pins:
                if pin.title is not None:
                    latex_io.write("\\pin" +
                                   "{" + c(pin.title) + "}" +
                                   "{" + pin.suttas[0].begin + "}" +
                                   "{" + pin.suttas[-1].end + "}\n")

                for sutta in pin.suttas:
                    latex_io.write("\\sutta" +
                                   "{" + sutta.begin + "}" +
                                   "{" + sutta.end + "}" +
                                   "{" + c(sutta.title) + "}\n")

                    for body_listline in sutta.body_lines:
                        latex_io.write(pdf.join_to_tex(body_listline, bns, c))

                        latex_io.write("\n\n")
                    latex_io.write("\n\n")
                latex_io.write("\n\n")
            latex_io.write("\\page\n\n")


def write_localnotes(latex_io: typing.TextIO, notes, bns, c):
    for subnote in notes:
        latex_io.write("\\startitemgroup[noteitems]\n")
        latex_io.write("\\item " +
                       "\\subnoteref{" + atom_note.localnote_label(notes.index(subnote)) + "}" +
                       pdf.join_to_tex(subnote, bns, c) + "\n")
        latex_io.write("\\stopitemgroup\n\n")


def write_globalnotes(latex_io: typing.TextIO, bns, c):
    notes = atom_note.get()
    for notekey, note in notes.items():
        # latex_io.write("\\startNote\n")
        latex_io.write("\\startitemgroup[noteitems]\n")
        for subnotekey, line in note.items():
            latex_io.write("\\item " +
                           "\\subnoteref{" + atom_note.globalnote_label(notekey, subnotekey) + "}" +
                           "\\subnotekey{" + (subnotekey or "\\null") + "}" +
                           pdf.join_to_tex(line, bns, c) + "\n")
        latex_io.write("\\stopitemgroup\n\n")


def build(sources_dir, out_dir, tex_filename, context_bin_path, lang):
    my_env = os.environ.copy()
    my_env["PATH"] = os.path.expanduser(context_bin_path) + ":" + my_env["PATH"]
    compile_cmd = "context --path={} {}/{} --mode={}".format(sources_dir, sources_dir, tex_filename, lang)

    stdout_file = open(os.path.join(out_dir, "cmd_stdout"), "w")
    stderr_file = open(os.path.join(out_dir, "cmd_stderr"), "w")

    def _run():
        print("running command:", compile_cmd, end=" ", flush=True)
        p = subprocess.Popen(compile_cmd, cwd=out_dir, shell=True, env=my_env,
                             stdout=stdout_file, stderr=stderr_file)
        p.communicate()
        if p.returncode != 0:
            input("command run wrong")
        print("done!")
    _run()
    stdout_file.close()
    stderr_file.close()


def make_keys():
    pass


def make(lang, temprootdir, context_bin_path, fonts_dir, bookdir):
    bns = [sn.BN]
    if lang == pyccc.pdf.TC:
        c = lang_convert.do_nothing
    else:  # lang == pyccc.pdf.SC:
        c = lang_convert.convert2sc

    mytemprootdir = os.path.join(temprootdir, "sn_" + lang)

    if True:
        nikaya = sn.get()
        sources_dir = os.path.join(mytemprootdir, "work")
        os.makedirs(sources_dir, exist_ok=True)
        out_dir = os.path.join(mytemprootdir, "out")
        os.makedirs(out_dir, exist_ok=True)

        write_fontstex(sources_dir, fonts_dir)

        with open(sources_dir + "/" + main_filename, "w") as f:
            write_main(f, bns, c)

        with open(sources_dir + "/" + suttas_filename, "w") as f:
            write_suttas(f, bns, c)

        with open(sources_dir + "/" + localnotes_filename, "w") as f:
            write_localnotes(f, nikaya.local_notes, bns, c)

        with open(sources_dir + "/" + globalnotes_filename, "w") as f:
            write_globalnotes(f, bns, c)

        shutil.copy(os.path.join(pyccc.TEX_DIR, read_note_filename), sources_dir)
        shutil.copy(os.path.join(pyccc.TEX_DIR, creator_note_filename), sources_dir)

        build(sources_dir=sources_dir, out_dir=out_dir, tex_filename=main_filename,
              context_bin_path=context_bin_path, lang=lang)
        # shutil.move(os.path.join(out_dir, "sn.pdf"), os.path.join(bookdir, "sn_tc_eb.pdf"))